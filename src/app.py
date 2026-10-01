#!/usr/bin/env python3
"""The Corsu window: switch each part of the translation on or off, pause the terminal, add programs.

Uses Tk when Python has it (Windows, macOS), otherwise the desktop's own dialogs (kdialog on KDE, zenity
elsewhere), otherwise a menu in the terminal.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import corsu
from installer import t

LABELS = {
    'firefox': ('Firefox', 'Firefox'),
    'chromium': ('Chrome, Opera GX and other browsers', 'Chrome, Opera GX et autres navigateurs'),
    'discord': ('Discord', 'Discord'),
    'vesktop': ('Vesktop', 'Vesktop'),
    'desktop': ('KDE desktop and programs', 'Bureau et programmes KDE'),
    'terminal': ('Terminal commands', 'Commandes du terminal'),
}


def parts():
    """(name, label, is in Corsican) for every part that can be switched."""
    state = corsu.load_state()
    return [(name, t(*LABELS[name]), not corsu.is_disabled(name, state)) for name in corsu.switchable(state)]


def apply(wanted):
    """Switch on what is in `wanted`, off what is not. Returns a short report."""
    current = {name: on for name, _, on in parts()}
    turn_on = [name for name, on in current.items() if name in wanted and not on]
    turn_off = [name for name, on in current.items() if name not in wanted and on]
    if turn_off:
        corsu.disable(turn_off)
    if turn_on:
        corsu.enable(turn_on)
    if not (turn_on or turn_off):
        return t('Nothing to change.', 'Rien à changer.')
    return t('Done. Restart the programs concerned.', 'C\'est fait. Redémarrez les logiciels concernés.')


def pause_terminal(hours=1):
    corsu.disable(['terminal'], hours=hours)
    return t(f'The terminal is back in French for {hours} hour(s), in new windows.',
             f'Le terminal repasse en français pendant {hours} heure(s), dans les nouvelles fenêtres.')


def open_setup():
    """Start the installer menu in a terminal window, to add or remove programs."""
    command = [sys.executable, str(corsu.SRC / 'installer.py')]
    if corsu.PLATFORM == 'windows':
        python = Path(sys.executable).with_name('python.exe')
        subprocess.Popen(['cmd', '/c', 'start', 'Corsu', str(python if python.exists() else sys.executable),
                          str(corsu.SRC / 'installer.py')])
    elif corsu.PLATFORM == 'macos':
        script = ' '.join(f"'{part}'" for part in command)
        subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{script}"',
                          '-e', 'tell application "Terminal" to activate'])
    else:
        for terminal in (['konsole', '-e'], ['gnome-terminal', '--'], ['xfce4-terminal', '-x'],
                         ['x-terminal-emulator', '-e'], ['xterm', '-e']):
            if shutil.which(terminal[0]):
                subprocess.Popen([*terminal, *command])
                return
        subprocess.Popen(command)


def uninstall_in_terminal():
    command = [sys.executable, str(corsu.SRC / 'installer.py'), '--uninstall']
    if corsu.PLATFORM == 'linux':
        for terminal in (['konsole', '-e'], ['gnome-terminal', '--'], ['x-terminal-emulator', '-e'], ['xterm', '-e']):
            if shutil.which(terminal[0]):
                subprocess.Popen([*terminal, *command])
                return
    subprocess.Popen(command)


def run_tk():
    import tkinter
    from tkinter import ttk, messagebox

    window = tkinter.Tk()
    window.title('Corsu')
    frame = ttk.Frame(window, padding=16)
    frame.grid()
    ttk.Label(frame, text=t('In Corsican:', 'En corse :'), font=('', 12, 'bold')).grid(sticky='w')
    variables = {}
    for name, label, on in parts():
        variables[name] = tkinter.BooleanVar(value=on)
        ttk.Checkbutton(frame, text=label, variable=variables[name]).grid(sticky='w', pady=2)
    status = ttk.Label(frame, text='', wraplength=360)

    def report(text):
        status.configure(text=text)

    def run(action):
        try:
            report(action())
        except Exception as error:  # Shown to the person instead of a silent failure.
            messagebox.showerror('Corsu', str(error))
        for name, _, on in parts():
            variables[name].set(on)

    buttons = ttk.Frame(frame)
    buttons.grid(sticky='we', pady=(12, 0))
    ttk.Button(buttons, text=t('Apply', 'Appliquer'),
               command=lambda: run(lambda: apply({name for name, var in variables.items() if var.get()}))).grid(row=0, column=0)
    if 'terminal' in variables:
        ttk.Button(buttons, text=t('Terminal in French for 1 hour', 'Terminal en français 1 heure'),
                   command=lambda: run(pause_terminal)).grid(row=0, column=1, padx=6)
    ttk.Button(frame, text=t('Add or remove programs…', 'Ajouter ou retirer des logiciels…'),
               command=open_setup).grid(sticky='w', pady=(12, 0))
    ttk.Button(frame, text=t('Remove Corsu…', 'Retirer Corsu…'), command=uninstall_in_terminal).grid(sticky='w', pady=(4, 0))
    status.grid(sticky='w', pady=(12, 0))
    window.mainloop()


def run_dialogs(tool):
    """kdialog or zenity: a menu of actions, then a checklist."""
    while True:
        actions = [('switch', t('Choose what is in Corsican', 'Choisir ce qui est en corse'))]
        if 'terminal' in corsu.switchable():
            actions.append(('pause', t('Terminal in French for 1 hour', 'Terminal en français pendant 1 heure')))
        actions += [('setup', t('Add or remove programs', 'Ajouter ou retirer des logiciels')),
                    ('remove', t('Remove Corsu', 'Retirer Corsu'))]
        if tool == 'kdialog':
            command = ['kdialog', '--title', 'Corsu', '--menu', 'Corsu', *[item for pair in actions for item in pair]]
        else:
            command = ['zenity', '--list', '--title', 'Corsu', '--column', 'id', '--column', 'Corsu',
                       '--hide-column', '1', '--print-column', '1', *[item for pair in actions for item in pair]]
        choice = subprocess.run(command, capture_output=True, text=True).stdout.strip()
        if not choice:
            return
        if choice == 'switch':
            items = parts()
            if tool == 'kdialog':
                command = ['kdialog', '--title', 'Corsu', '--checklist', t('In Corsican:', 'En corse :'),
                           *[value for name, label, on in items for value in (name, label, 'on' if on else 'off')]]
            else:
                command = ['zenity', '--list', '--checklist', '--title', 'Corsu', '--text', t('In Corsican:', 'En corse :'),
                           '--column', '', '--column', 'id', '--column', '', '--hide-column', '2', '--print-column', '2',
                           '--separator', ' ', *[value for name, label, on in items for value in ('TRUE' if on else 'FALSE', name, label)]]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                continue
            message = apply(set(result.stdout.replace('"', ' ').split()))
        elif choice == 'pause':
            message = pause_terminal()
        elif choice == 'setup':
            open_setup()
            return
        else:
            uninstall_in_terminal()
            return
        if tool == 'kdialog':
            subprocess.run(['kdialog', '--title', 'Corsu', '--msgbox', message])
        else:
            subprocess.run(['zenity', '--info', '--title', 'Corsu', '--text', message])


def run_text():
    while True:
        print('\nCorsu')
        items = parts()
        for number, (name, label, on) in enumerate(items, 1):
            print(f'  [{"x" if on else " "}] {number}. {label}')
        print(t('  p. Terminal in French for 1 hour   s. Add or remove programs   q. Quit',
                '  p. Terminal en français 1 heure   s. Ajouter ou retirer des logiciels   q. Quitter'))
        answer = input(t('Type a number to switch it, or a letter: ', 'Tapez un numéro pour l\'inverser, ou une lettre : ')).strip().lower()
        if answer in ('q', ''):
            return
        if answer == 'p':
            print(pause_terminal())
        elif answer == 's':
            os.execv(sys.executable, [sys.executable, str(corsu.SRC / 'installer.py')])
        elif answer.isdigit() and 1 <= int(answer) <= len(items):
            name, _, on = items[int(answer) - 1]
            wanted = {n for n, _, o in items if o}
            wanted.symmetric_difference_update({name})
            print(apply(wanted))


def main():
    if not corsu.STATE.exists():
        # Nothing installed yet: go straight to the installer.
        os.execv(sys.executable, [sys.executable, str(corsu.SRC / 'installer.py'), *[a for a in sys.argv[1:] if a != '--text']])
    if '--text' not in sys.argv:
        try:
            import tkinter  # noqa: F401
            tkinter.Tk().destroy()
            return run_tk()
        except Exception:
            pass
        for tool in ('kdialog', 'zenity'):
            if shutil.which(tool) and os.environ.get('DISPLAY', os.environ.get('WAYLAND_DISPLAY')):
                return run_dialogs(tool)
        if not sys.stdin.isatty() and corsu.PLATFORM == 'linux':
            for terminal in (['konsole', '-e'], ['gnome-terminal', '--'], ['x-terminal-emulator', '-e'], ['xterm', '-e']):
                if shutil.which(terminal[0]):
                    os.execvp(terminal[0], [*terminal, sys.executable, str(Path(__file__).resolve()), '--text'])
    return run_text()


if __name__ == '__main__':
    main()
