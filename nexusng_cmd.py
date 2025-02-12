# version ohne offline function
import os
import sys
import time
import json
import requests
import random
import shutil
import getpass
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.box import DOUBLE
from rich.align import Align
from rich.style import Style
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.theme import Theme
import ctypes

# Custom theme for a more professional look
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "primary": "bold blue",
    "secondary": "cyan",
    "accent": "bold yellow",  # Changed from 'accent' to 'bold yellow'
})

# Initialize Rich console with custom theme
console = Console(theme=custom_theme)

# Directory for chat storage and settings
CHATS_DIR = os.path.join(os.path.expanduser("~"), ".nexusng_chats")

# Settings file
SETTINGS_FILE = os.path.join(CHATS_DIR, "settings.json")

# API key file
API_KEY_FILE = os.path.join(CHATS_DIR, "api_key.txt")

# DeepSeek API Configuration
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Set CMD window title
ctypes.windll.kernel32.SetConsoleTitleW("NexusNG-CMD")

def set_console_size():
    os.system('mode con: cols=100 lines=30')

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {"preferred_name": "User"}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_api_key(api_key):
    with open(API_KEY_FILE, 'w') as f:
        f.write(api_key)

def verify_api_key(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Test"}]
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False

def prompt_for_api_key():
    while True:
        console.print(Panel.fit(
            "[warning]No valid DeepSeek API key found.[/warning]\n"
            "Please enter your DeepSeek API key to continue.",
            title="API Key Required",
            border_style="danger",
            padding=(1, 1)
        ))
        api_key = getpass.getpass("Enter your DeepSeek API key (input will be hidden): ")
        if verify_api_key(api_key):
            save_api_key(api_key)
            return api_key
        else:
            console.print("[danger]Invalid API key. Please try again.[/danger]")
            time.sleep(2)

def generate_response(prompt, chat_history, preferred_name, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_message = f"""You are NexusNG-CMD, the CMD version of the NexusNG. Unlike the full NexusNG version, you don't use the NexusNG database. Instead, you rely on an API key from DeepSeek to avoid unnecessary resource consumption from NexusNG. If users want the full experience, they should visit https://nexusng.site.

You are still an open-source tool developed by Tuco, available for everyone to use. You retain memory of previous messages to offer better responses, and your main purpose is to support with programming, user interface design, and other technical projects. Always address the user as {preferred_name}.

If asked about NexusNG, provide the official website https://nexusng.site or invite users to join the Discord community at https://discord.gg/nexusng. If asked about Tuco, refer them to https://tucot9.com."""
    
    messages = [{"role": "system", "content": system_message}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})


    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": "deepseek-chat",
        "messages": messages
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        else:
            return "Sorry, I couldn't generate a response. Please try again."
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
            return "ERROR: Invalid API key. Please update your API key in the settings menu."
        else:
            return f"Error: {str(e)}"

def print_animated(text, delay=0.03):
    for char in text:
        console.print(char, end="", style="secondary")
        console.file.flush()
        time.sleep(delay)
    console.print()

def save_chat(chat_name, messages):
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)
    with open(os.path.join(CHATS_DIR, f"{chat_name}.json"), "w") as f:
        json.dump(messages, f)

def load_chat(chat_name):
    try:
        with open(os.path.join(CHATS_DIR, f"{chat_name}.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def list_chats():
    if not os.path.exists(CHATS_DIR):
        return []
    return [f.split('.')[0] for f in os.listdir(CHATS_DIR) if f.endswith('.json') and f != "settings.json"]

def display_chat_history(messages):
    table = Table(show_header=False, expand=True, box=DOUBLE, border_style="primary")
    for msg in messages:
        if msg['role'] == 'user':
            table.add_row(Panel(msg['content'], style="bold yellow", title="You", border_style="yellow"))
        elif msg['role'] == 'assistant':
            table.add_row(Panel(Markdown(msg['content']), style="secondary", title="NexusNG-CMD", border_style="secondary"))
    console.print(table)

def chat_interface(chat_name, messages, settings, api_key):
    while True:
        console.clear()
        display_chat_history(messages)
        user_input = Prompt.ask(f"\n[bold yellow]{settings['preferred_name']}")
        
        if user_input.lower() in ['exit', 'quit']:
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[secondary]NexusNG-CMD is processing...", total=None)
            ai_response = generate_response(user_input, messages, settings['preferred_name'], api_key)
        
        if ai_response.startswith("ERROR: Invalid API key"):
            console.print("[danger]" + ai_response + "[/danger]")
            input("\nPress Enter to return to the main menu...")
            return
        
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": ai_response})
        
        print_animated(ai_response)
        
        save_chat(chat_name, messages)
        input("\nPress Enter to continue...")

def display_menu():
    menu_style = "bold cyan"
    menu = Text()
    menu.append("1. ", style="yellow")
    menu.append("Start a new chat\n", style=menu_style)
    menu.append("2. ", style="yellow")
    menu.append("Continue existing chat\n", style=menu_style)
    menu.append("3. ", style="yellow")
    menu.append("List all chats\n", style=menu_style)
    menu.append("4. ", style="yellow")
    menu.append("Settings\n", style=menu_style)
    menu.append("5. ", style="yellow")
    menu.append("Exit", style=menu_style)
    
    panel = Panel(
        Align.center(menu),
        title="[bold blue]NexusNG-CMD[/bold blue]",
        subtitle="[italic cyan]Your Professional AI Assistant[/italic cyan]",
        border_style="primary",
        padding=(1, 1)
    )
    return panel

def initialization_animation():
    loading_time = random.uniform(3, 6)
    steps = 100
    step_time = loading_time / steps

    with Progress(
        SpinnerColumn(),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[secondary]Initializing NexusNG-CMD...", total=steps)

        for _ in range(steps):
            time.sleep(step_time)
            progress.update(task, advance=1)

            # Simulate initialization process with professional messages
            if random.random() < 0.1:
                progress.console.print("[info]Loading language models...[/info]")
            elif random.random() < 0.05:
                progress.console.print("[info]Optimizing response algorithms...[/info]")
            elif random.random() < 0.02:
                progress.console.print("[info]Calibrating AI parameters...[/info]")

    console.print("\n[success]NexusNG-CMD initialized successfully![/success]")
    time.sleep(1)

def settings_menu(settings, api_key):
    while True:
        console.clear()
        console.print(Panel.fit(
            f"[secondary]Current Settings:[/secondary]\n"
            f"Preferred Name: {settings['preferred_name']}\n"
            f"Chat Storage Location: {CHATS_DIR}\n"
            f"API Key: {'*' * 20 + api_key[-4:] if api_key else 'Not set'}\n\n"
            "[yellow]1.[/yellow] Change Preferred Name\n"
            "[yellow]2.[/yellow] Change API Key\n"
            "[yellow]3.[/yellow] Delete All Data\n"
            "[yellow]4.[/yellow] Back to Main Menu",
            title="Settings",
            border_style="primary",
            padding=(1, 1)
        ))
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            new_name = Prompt.ask("Enter your preferred name")
            settings['preferred_name'] = new_name
            save_settings(settings)
            console.print("[success]Preferred name updated successfully![/success]")
        elif choice == "2":
            new_api_key = getpass.getpass("Enter your new DeepSeek API key (input will be hidden): ")
            save_api_key(new_api_key)
            api_key = new_api_key
            console.print("[success]API key updated successfully![/success]")
        elif choice == "3":
            if Confirm.ask("Are you sure you want to delete all data? This action cannot be undone."):
                shutil.rmtree(CHATS_DIR)
                os.makedirs(CHATS_DIR)
                settings = {"preferred_name": "User"}
                save_settings(settings)
                api_key = None
                console.print("[success]All data has been deleted successfully![/success]")
            else:
                console.print("[warning]Data deletion cancelled.[/warning]")
        elif choice == "4":
            return settings, api_key
        
        input("\nPress Enter to continue...")

def main():
    set_console_size()
    console.clear()
    console.print(Panel.fit(
        "[bold blue]Welcome to NexusNG-CMD[/bold blue]\n"
        "[italic cyan]Developed by TucoT9[/italic cyan]",
        border_style="blue",
        padding=(1, 1),
        title="NexusNG-CMD",
        subtitle="Your Professional AI Assistant"
    ))
    time.sleep(1)
    
    api_key = load_api_key()
    if not api_key or not verify_api_key(api_key):
        api_key = prompt_for_api_key()
    
    initialization_animation()
    
    settings = load_settings()
    
    while True:
        console.clear()
        console.print(display_menu())
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "5":
            print_animated("Thank you for using NexusNG-CMD. Goodbye!", delay=0.05)
            time.sleep(1)
            sys.exit(0)
        elif choice == "1":
            current_chat = Prompt.ask("Enter new chat name")
            messages = []
            chat_interface(current_chat, messages, settings, api_key)
        elif choice == "2":
            chats = list_chats()
            if not chats:
                console.print("[warning]No existing chats found. Starting a new chat.[/warning]")
                current_chat = Prompt.ask("Enter new chat name")
                messages = []
            else:
                table = Table(title="Existing Chats", box=DOUBLE, border_style="primary")
                table.add_column("Number", style="yellow", no_wrap=True)
                table.add_column("Chat Name", style="secondary")
                for i, chat in enumerate(chats, 1):
                    table.add_row(str(i), chat)
                console.print(table)
                chat_choice = Prompt.ask("Choose a chat number", choices=[str(i) for i in range(1, len(chats)+1)])
                current_chat = chats[int(chat_choice)-1]
                messages = load_chat(current_chat)
            chat_interface(current_chat, messages, settings, api_key)
        elif choice == "3":
            chats = list_chats()
            if not chats:
                console.print("[warning]No existing chats found.[/warning]")
            else:
                table = Table(title="All Chats", box=DOUBLE, border_style="primary")
                table.add_column("Chat Name", style="secondary")
                for chat in chats:
                    table.add_row(chat)
                console.print(table)
            input("\nPress Enter to continue...")
        elif choice == "4":
            settings, api_key = settings_menu(settings, api_key)

if __name__ == "__main__":
    main()

