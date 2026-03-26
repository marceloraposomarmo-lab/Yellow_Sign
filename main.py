#!/usr/bin/env python3
"""
THE KING IN YELLOW — Entry Point
A Lovecraftian Dungeon Crawler (Python Terminal Edition)
"""

import random
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_data import CLASSES, EVENTS, TRAPS, MAX_ACTIVE_SKILLS
from game_engine import (
    GameState, generate_item, start_combat, player_use_skill,
    enemy_turn, process_status_effects, process_player_status_effects,
    tick_player_buffs, check_boss_phase, combat_run_attempt,
    generate_paths, advance_floor, get_floor_narrative,
    resolve_event, resolve_trap, generate_shop, buy_shop_item,
)
from ui import GameUI
from save_system import save_game, load_game, list_saves


def get_choice(prompt, valid_range, extra_commands=None):
    """Get a numeric choice or command from the player."""
    extra_commands = extra_commands or {}
    while True:
        try:
            raw = ui.input(prompt).strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)
        if raw in extra_commands:
            return extra_commands[raw]
        try:
            val = int(raw)
            if val in valid_range:
                return val
        except ValueError:
            pass
        ui.print("[red]Invalid choice.[/red]" if hasattr(ui, 'console') else "Invalid choice.")


def title_screen():
    """Handle the title screen."""
    while True:
        ui.show_title()
        choice = get_choice("Choose", [1, 2, 3, 4])
        if choice == 1:
            return "new"
        elif choice == 2:
            return "load"
        elif choice == 3:
            ui.show_about()
            ui.pause()
        elif choice == 4:
            return "quit"


def class_select():
    """Handle class selection."""
    class_ids = ui.show_class_select()
    choice = get_choice("Choose your class", range(1, len(class_ids) + 1))
    return class_ids[choice - 1]


def load_screen():
    """Handle loading a saved game."""
    ui.show_save_menu()
    saves = list_saves()
    ui.print("")
    valid_slots = [sv["slot"] for sv in saves if not sv.get("empty") and not sv.get("error")]
    if not valid_slots:
        ui.print("[dim]No saves found.[/dim]" if hasattr(ui, 'console') else "No saves found.")
        ui.pause()
        return None
    all_slots = list(range(5))
    choice = get_choice("Load slot (or 0 to cancel", [0] + all_slots)
    if choice == 0:
        return None
    state = load_game(choice)
    if state:
        return state
    ui.print("[red]Failed to load save.[/red]" if hasattr(ui, 'console') else "Failed to load save.")
    ui.pause()
    return None


def save_screen(state):
    """Handle saving the game."""
    ui.show_save_menu()
    ui.print("")
    choice = get_choice("Save to slot (or 0 to cancel", [0, 1, 2, 3, 4])
    if choice == 0:
        return
    path = save_game(state, choice)
    if HAS_RICH_MSG:
        ui.print(f"[green]Game saved to slot {choice}![/green]")
    else:
        print(f"Game saved to slot {choice}!")
    ui.pause("Saved! Press Enter...")


def handle_inventory(state):
    """Handle inventory management."""
    while True:
        ui.show_inventory()
        raw = ui.input("Action").strip().upper()
        if raw == "Q" or raw == "":
            break
        elif raw.startswith("D "):
            try:
                idx = int(raw[2:]) - 1
                if 0 <= idx < len(state.inventory):
                    removed = state.inventory.pop(idx)
                    if HAS_RICH_MSG:
                        ui.print(f"[dim]Discarded {removed.name}.[/dim]")
                    else:
                        print(f"Discarded {removed.name}.")
            except (ValueError, IndexError):
                pass
        else:
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(state.inventory):
                    item = state.inventory[idx]
                    prev = state.equip_item(item)
                    state.inventory.pop(idx)
                    if prev:
                        state.inventory.append(prev)
                    if HAS_RICH_MSG:
                        ui.print(f"[green]Equipped {item.name}![/green]")
                    else:
                        print(f"Equipped {item.name}!")
            except (ValueError, IndexError):
                pass


def handle_levelup(state):
    """Handle level-up skill selection."""
    while state.pending_levelup_skills:
        ui.show_levelup()
        n_skills = len(state.pending_levelup_skills)
        choice = get_choice("Choose", range(1, n_skills + 2))
        if choice == n_skills + 1:
            # Skip
            state.pending_levelup_skills = []
            break
        chosen = state.pending_levelup_skills[choice - 1]

        if len(state.active_skills) >= MAX_ACTIVE_SKILLS:
            # Need to replace
            ui.show_replace_skill()
            n_active = len(state.active_skills)
            rep_choice = get_choice("Replace", range(1, n_active + 2))
            if rep_choice == n_active + 1:
                # Cancel back to choices
                continue
            state.active_skills[rep_choice - 1] = chosen
        else:
            state.active_skills.append(chosen)

        state.pending_levelup_skills = []
        if HAS_RICH_MSG:
            ui.print(f"[green]Learned {chosen.name}![/green]")
        else:
            print(f"Learned {chosen.name}!")
        ui.pause()


def explore_loop(state):
    """Main exploration and game loop."""
    while True:
        # Show explore screen
        is_boss = state.floor >= state.max_floor
        ui.show_explore()

        if is_boss:
            # Boss fight
            ui.pause("Press Enter to face the King...")
            start_combat(state, is_boss=True)
            result = combat_loop(state)
            if result == "victory":
                ui.show_victory()
                ui.pause()
                return "victory"
            elif result == "gameover":
                return "gameover"
            continue

        # Generate paths
        paths = generate_paths(state.floor)
        ui.show_path_choices(paths)
        valid = list(range(1, len(paths) + 1))
        choice = get_choice("Choose your path", valid,
                            {"I": "inventory", "S": "save"})

        if choice == "inventory":
            handle_inventory(state)
            continue
        elif choice == "save":
            save_screen(state)
            continue

        path = paths[choice - 1]
        state.rooms_explored += 1
        if state.add_madness(2):
            ui.show_gameover("Your mind shatters. The Yellow Sign consumes your last rational thought.")
            ui.pause()
            return "gameover"

        ptype = path["type"]
        if ptype == "combat":
            start_combat(state, is_boss=False)
            result = combat_loop(state)
            if result == "victory":
                continue  # after_combat_reward handled inside
            elif result == "gameover":
                return "gameover"
            elif result == "fled":
                continue

        elif ptype == "event":
            event = random.choice(EVENTS)
            ui.show_event(event)
            ev_idx = EVENTS.index(event)
            n_outcomes = len(event["outcomes"])
            choice = get_choice("Choose", range(1, n_outcomes + 1))
            msg, loot = resolve_event(state, ev_idx, choice - 1)
            if HAS_RICH_MSG:
                ui.print(f"\n[bold]{msg}[/bold]")
            else:
                print(f"\n{msg}")
            if loot:
                state.inventory.append(loot)
                if HAS_RICH_MSG:
                    ui.print(f"[green]Received: {loot.name}[/green]")
                else:
                    print(f"Received: {loot.name}")
            if state.hp <= 0:
                ui.show_gameover("The asylum claims another victim.")
                ui.pause()
                return "gameover"
            ui.pause()

        elif ptype == "loot":
            count = 1 + (1 if random.random() < 0.3 else 0)
            items = [generate_item(state.floor, luck=state.luck) for _ in range(count)]
            gf = 5 + random.randint(0, 10) + state.floor * 2
            state.gold += gf
            ui.show_loot(items, gold_found=gf)
            choice = get_choice("Choose", range(1, len(items) + 2))
            if choice <= len(items):
                item = items[choice - 1]
                if len(state.inventory) < 20:
                    state.inventory.append(item)
                    if HAS_RICH_MSG:
                        ui.print(f"[green]Picked up {item.name}![/green]")
                    else:
                        print(f"Picked up {item.name}!")
                else:
                    # Auto-equip if inventory full
                    prev = state.equip_item(item)
                    if prev:
                        state.inventory.append(prev)
                    if HAS_RICH_MSG:
                        ui.print(f"[green]Inventory full — equipped {item.name}![/green]")
                    else:
                        print(f"Inventory full — equipped {item.name}!")
            else:
                if HAS_RICH_MSG:
                    ui.print("[dim]Left it behind.[/dim]")
                else:
                    print("Left it behind.")
            ui.pause()

        elif ptype == "rest":
            ui.show_rest()
            choice = get_choice("Choose", [1, 2, 3])
            if choice == 1:
                h = int(state.max_hp * 0.4)
                state.hp = min(state.max_hp, state.hp + h)
                if HAS_RICH_MSG:
                    ui.print(f"[green]Rested. Healed {h} HP.[/green]")
                else:
                    print(f"Rested. Healed {h} HP.")
            elif choice == 2:
                state.add_madness(-15)
                if HAS_RICH_MSG:
                    ui.print("[green]Meditated. Madness reduced.[/green]")
                else:
                    print("Meditated. Madness reduced.")
            elif choice == 3:
                for k in state.base_stats:
                    state.base_stats[k] += 1
                state.recalc_stats()
                if HAS_RICH_MSG:
                    ui.print("[green]Trained. All stats +1.[/green]")
                else:
                    print("Trained. All stats +1.")
            ui.pause()
            # Advance floor
            if advance_floor(state):
                ui.show_victory()
                ui.pause()
                return "victory"
            continue

        elif ptype == "shop":
            shop_items, shop_prices = generate_shop(state)
            shop_sold = [False] * len(shop_items)
            while True:
                ui.show_shop(shop_items, shop_prices, shop_sold)
                choice = get_choice("Buy", range(1, len(shop_items) + 2))
                if choice == len(shop_items) + 1:
                    break
                idx = choice - 1
                ok, msg = buy_shop_item(state, shop_items, shop_prices, shop_sold, idx)
                if HAS_RICH_MSG:
                    ui.print(f"[{'green' if ok else 'red'}]{msg}[/]")
                else:
                    print(msg)
                ui.pause()
            if advance_floor(state):
                ui.show_victory()
                ui.pause()
                return "victory"
            continue

        elif ptype == "trap":
            trap = random.choice(TRAPS)
            trap_idx = TRAPS.index(trap)
            msg, game_over = resolve_trap(state, trap_idx)
            if HAS_RICH_MSG:
                ui.console.print(f"\n[bold yellow]⚠ {trap['name']} ⚠[/bold yellow]")
                ui.console.print(f"[dim]{trap['desc']}[/dim]")
                ui.print(f"\n{msg}")
            else:
                print(f"\n  ⚠ {trap['name']} ⚠")
                print(f"  {trap['desc']}")
                print(f"\n  {msg}")
            if game_over:
                ui.show_gameover("The trap claims your life.")
                ui.pause()
                return "gameover"
            ui.pause()
            if advance_floor(state):
                ui.show_victory()
                ui.pause()
                return "victory"
            continue

        # Advance floor for combat/event/loot (handled in end_combat)
        pass


def combat_loop(state):
    """Handle turn-based combat. Returns 'victory', 'gameover', or 'fled'."""
    while True:
        ui.show_combat()
        c = state.combat
        if not c:
            return "gameover"

        e = c.enemy
        if e.hp <= 0:
            return end_combat(state, victory=True)

        if state.hp <= 0:
            return end_combat(state, victory=False)

        if c.turn == "player":
            n_skills = len(state.active_skills)
            valid = list(range(1, n_skills + 1))
            choice = get_choice("Action", valid,
                                {"R": "run", "I": "inventory", "S": "save"})

            if choice == "run":
                if c.is_boss:
                    if HAS_RICH_MSG:
                        ui.print("[red]Cannot flee from the King![/red]")
                    else:
                        print("Cannot flee from the King!")
                    ui.pause("Press Enter...")
                    continue
                if combat_run_attempt(state):
                    if HAS_RICH_MSG:
                        ui.print("[yellow]You flee![/yellow]")
                    else:
                        print("You flee!")
                    state.combat = None
                    if advance_floor(state):
                        return "victory"
                    return "fled"
                else:
                    if HAS_RICH_MSG:
                        ui.print("[red]Failed to escape![/red]")
                    else:
                        print("Failed to escape!")
                    # Enemy turn after failed flee
                    c.turn = "enemy"
                    ui.pause("Press Enter...")
                    continue

            elif choice == "inventory":
                handle_inventory(state)
                continue
            elif choice == "save":
                save_screen(state)
                continue

            # Use skill
            sk = state.active_skills[choice - 1]
            if sk.current_cd > 0:
                if HAS_RICH_MSG:
                    ui.print("[red]That ability is on cooldown![/red]")
                else:
                    print("That ability is on cooldown!")
                ui.pause("Press Enter...")
                continue

            logs = player_use_skill(state, choice - 1)
            for text, log_type in logs:
                c.add_log(text, log_type)

            # Check boss phase
            phase_logs = check_boss_phase(state)
            for text, log_type in phase_logs:
                c.add_log(text, log_type)

            # Tick player buffs
            buff_logs = tick_player_buffs(state)
            for text, log_type in buff_logs:
                c.add_log(text, log_type)

            # Process enemy status effects
            se_logs = process_status_effects(e, False, state)
            for text, log_type in se_logs:
                c.add_log(text, log_type)

            # Check if enemy died
            if e.hp <= 0:
                ui.show_combat()
                ui.pause("Enemy defeated! Press Enter...")
                return end_combat(state, victory=True)

            # Check boss phase again
            phase_logs = check_boss_phase(state)
            for text, log_type in phase_logs:
                c.add_log(text, log_type)

            c.turn = "enemy"

        else:  # enemy turn
            ui.pause("Enemy's turn. Press Enter...")
            logs = enemy_turn(state)
            for text, log_type in logs:
                c.add_log(text, log_type)

            # Check if player died (but undying might save them)
            if state.hp <= 0:
                ui.show_combat()
                ui.pause("You fall... Press Enter...")
                return end_combat(state, victory=False)

            # Process player status effects
            se_logs = process_player_status_effects(state)
            for text, log_type in se_logs:
                c.add_log(text, log_type)

            if state.hp <= 0:
                ui.show_combat()
                ui.pause("You fall... Press Enter...")
                return end_combat(state, victory=False)

            # Tick cooldowns
            for sk in state.active_skills:
                if sk.current_cd > 0:
                    sk.current_cd -= 1

            # Tick player buffs
            buff_logs = tick_player_buffs(state)
            for text, log_type in buff_logs:
                c.add_log(text, log_type)

            c.turn = "player"
            c.turn_count += 1


def end_combat(state, victory):
    """Handle end of combat."""
    c = state.combat
    if not c:
        return "gameover"

    if victory:
        state.kills += 1
        xp_g = 12 + state.floor * 4 + (80 if c.is_boss else 0)
        gold_g = 6 + random.randint(0, 8) + state.floor * 2 + (50 if c.is_boss else 0)
        state.xp += xp_g
        state.gold += gold_g
        state.add_madness(-15 if c.is_boss else 3)

        # Generate loot
        loot = generate_item(state.floor, luck=state.luck)

        # Check level up
        leveled = state.check_level_up()
        if leveled:
            handle_levelup(state)

        # Show loot
        ui.show_loot([loot], gold_found=gold_g, xp_found=xp_g)
        n = 1
        choice = get_choice("Choose", range(1, n + 2))
        if choice == 1:
            prev = state.equip_item(loot)
            if prev:
                state.inventory.append(prev)
            if HAS_RICH_MSG:
                ui.print(f"[green]Equipped {loot.name}![/green]")
            else:
                print(f"Equipped {loot.name}!")
        else:
            if len(state.inventory) < 20:
                state.inventory.append(loot)
                if HAS_RICH_MSG:
                    ui.print(f"[green]Kept {loot.name} in backpack.[/green]")
                else:
                    print(f"Kept {loot.name} in backpack.")
            else:
                if HAS_RICH_MSG:
                    ui.print("[dim]Left it behind.[/dim]")
                else:
                    print("Left it behind.")

        ui.pause()
        state.combat = None

        if c.is_boss:
            ui.show_victory()
            ui.pause()
            return "victory"

        if advance_floor(state):
            ui.show_victory()
            ui.pause()
            return "victory"

        return "victory"
    else:
        state.combat = None
        ui.show_gameover("Your body crumples. The last thing you see is the Yellow Sign, burning brighter than ever.")
        ui.pause()
        return "gameover"


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

ui = GameUI()
HAS_RICH_MSG = True  # Will be set properly below

def main():
    global HAS_RICH_MSG
    HAS_RICH_MSG = hasattr(ui, 'console')

    while True:
        action = title_screen()

        if action == "quit":
            ui.clear()
            if HAS_RICH_MSG:
                ui.console.print("[dim]Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.[/dim]")
                ui.console.print("[dim]The King in Yellow awaits your return.[/dim]")
            else:
                print("Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.")
                print("The King in Yellow awaits your return.")
            break

        if action == "load":
            state = load_screen()
            if not state:
                continue
        else:
            class_id = class_select()
            state = GameState()
            state.init_from_class(class_id)

        ui.state = state

        # Main game loop
        result = explore_loop(state)

        if result == "victory":
            pass  # Already shown victory screen
        elif result == "gameover":
            pass  # Already shown gameover screen

        # Ask to play again
        if HAS_RICH_MSG:
            ui.print("")
            again = ui.input("[bold]Play again? (Y/N)[/bold]").strip().upper()
        else:
            again = input("\nPlay again? (Y/N) ").strip().upper()

        if again != "Y":
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nThe Yellow Sign fades. For now.")
        sys.exit(0)
