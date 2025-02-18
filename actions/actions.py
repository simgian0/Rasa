import pandas as pd
import re
from serpapi import GoogleSearch
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
import difflib
import random
import asyncio
from fractions import Fraction

# Percorso dei dataset
DATASET_CHARACTER_PATH = "/home/arthas0130/Rasa/Dataset DnD/over_one_mil_chars.csv"  
DATASET_SPELLS_PATH = "/home/arthas0130/Rasa/Dataset DnD/dnd-spells.csv"
DATASET_EQUIPS_PATH = "/home/arthas0130/Rasa/Dataset DnD/dndbeyond_equips.csv"
DATASET_FAERUN_PATH = "/home/arthas0130/Rasa/Dataset DnD/Countries of Faerun.csv"
DATASET_MONSTER_FILTERED = "/home/arthas0130/Rasa/Dataset DnD/dnd_monsters_filtered.csv"
    
SERPAPI_API_KEY = "9a7de92580d0789996224397085372b3096e4b04abfc5fe58ddf44fb5cbd1347"

class ActionDescribeMonster(Action):
    def name(self):
        return "action_describe_monster"
    
    def run(self, dispatcher, tracker, domain):
        # Ottenere il nome del mostro dallo slot o dal messaggio
        #monster_name = tracker.get_slot("monster_name")

        # Caricare il dataset
        file_path = DATASET_MONSTER_FILTERED
        monsters_df = pd.read_csv(file_path)
        
        # Normalizzare i nomi dei mostri dal dataset
        monsters_df["normalized_name"] = monsters_df["name"].str.lower().str.replace("-", " ").str.strip()
        monster_names_from_data = monsters_df["normalized_name"].tolist()
        
        # Estrarre il messaggio dell'utente e normalizzarlo
        message = tracker.latest_message.get("text", "").lower()
        
        # Controlla se il messaggio contiene la parola "monster"
        if "monster" not in message:
            dispatcher.utter_message(text="Please specify a monster name by saying 'monster' followed by its name.")
            return []
        
        user_input = message.split("monster")[-1].strip()

        # Trovare il nome più simile utilizzando difflib
        closest_match = difflib.get_close_matches(user_input, monster_names_from_data, n=1, cutoff=0.4)
        if closest_match:
            # Convertire il nome normalizzato al formato originale del dataset
            monster_row = monsters_df[monsters_df["normalized_name"] == closest_match[0]]
            if not monster_row.empty:
                monster_name = monster_row.iloc[0]["name"]
            else:
                monster_name = ""
        else:
            monster_name = ""

        # Controllo finale: se non c'è un nome valido, invia un messaggio di errore
        if not monster_name:
            dispatcher.utter_message(text="I couldn't understand which monster you meant.")
            return []
        
        # Cercare il mostro nel dataset
        monster = monsters_df[monsters_df["name"].str.lower().str.strip() == monster_name.lower().strip()]
        
        if not monster.empty:
            # Estrarre le informazioni del mostro
            monster_type = monster.iloc[0]["type"]
            monster_size = monster.iloc[0]["size"]
            monster_align = monster.iloc[0].get("align", "Unknown")
            monster_url = monster.iloc[0].get("url", "No URL available")
            is_legendary = "Yes" if monster.iloc[0]["legendary"] == "Legendary" else "No"
            
            # Costruire la risposta
            response = (
                f"The monster '{monster_name}' is of type '{monster_type}', size '{monster_size}', "
                f"alignment '{monster_align}', and it is {'Legendary' if is_legendary == 'Yes' else 'not legendary'}."
                f"\nYou can find more details here: {monster_url}"
            )
        else:
            # Messaggio se il mostro non è trovato
            response = f"Sorry, I couldn't find any details about the monster '{monster_name}'. Please check the name and try again."
        
        # Rispondere all'utente
        dispatcher.utter_message(text=response)
        
        return [SlotSet("monster_name", monster_name)]

class ActionGetMonsterStats(Action):
    def name(self):
        return "action_get_monster_stats"

    def run(self, dispatcher, tracker, domain):
        # Ottieni il nome del mostro
        #monster_name = tracker.get_slot("monster_name")

        # Carica il dataset
        file_path = DATASET_MONSTER_FILTERED
        monsters_df = pd.read_csv(file_path)
        
        # Normalizzare i nomi dei mostri dal dataset
        monsters_df["normalized_name"] = monsters_df["name"].str.lower().str.replace("-", " ").str.strip()
        monster_names_from_data = monsters_df["normalized_name"].tolist()
        
        # Estrarre il messaggio dell'utente e normalizzarlo
        message = tracker.latest_message.get("text", "").lower()
        
        # Controlla se il messaggio contiene la parola "monster"
        if "monster" not in message:
            dispatcher.utter_message(text="Please specify a monster name by saying 'monster' followed by its name.")
            return []
        
        user_input = message.split("monster")[-1].strip()

        # Trovare il nome più simile utilizzando difflib
        closest_match = difflib.get_close_matches(user_input, monster_names_from_data, n=1, cutoff=0.4)
        if closest_match:
            # Convertire il nome normalizzato al formato originale del dataset
            monster_row = monsters_df[monsters_df["normalized_name"] == closest_match[0]]
            if not monster_row.empty:
                monster_name = monster_row.iloc[0]["name"]
            else:
                monster_name = ""
        else:
            monster_name = ""

        # Controllo finale: se non c'è un nome valido, invia un messaggio di errore
        if not monster_name:
            dispatcher.utter_message(text="I couldn't understand which monster you meant.")
            return []
        
        # Cercare il mostro nel dataset
        monster = monsters_df[monsters_df["name"].str.lower().str.strip() == monster_name.lower().strip()]
        
        if not monster.empty:
            monster = monster_row.iloc[0]
            stats = {
                        "HP": monster.get("hp", "Unknown"),
                        "AC": monster.get("ac", "Unknown"),
                        "Speed": monster.get("speed", "Unknown"),
                        "CR": monster.get("cr", "Unknown"),
                        "STR": monster.get("str", "Unknown"),
                        "DEX": monster.get("dex", "Unknown"),
                        "CON": monster.get("con", "Unknown"),
                        "INT": monster.get("int", "Unknown"),
                        "WIS": monster.get("wis", "Unknown"),
                        "CHA": monster.get("cha", "Unknown"),
                    }
            response = (
                        f"The monster '{monster['name']}' has the following stats:\n"
                        f"- HP: {stats['HP']}\n"
                        f"- AC: {stats['AC']}\n"
                        f"- Speed: {stats['Speed']}\n"
                        f"- Challenge Rating: {stats['CR']}\n"
                        f"- STR: {stats['STR']}, DEX: {stats['DEX']}, CON: {stats['CON']}\n"
                        f"- INT: {stats['INT']}, WIS: {stats['WIS']}, CHA: {stats['CHA']}"
                    )
        else:
            response = f"Sorry, I couldn't find stats for the monster '{monster_name}'."

        dispatcher.utter_message(text=response)
        return []

class ResetSlot(Action):

    def name(self):
        return "action_reset"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="All things reset.\nWhat do you want do do next?")
        return [AllSlotsReset()]

class ActionCharacterCreation(Action):
    def name(self):
        return "action_character_creation"

    def run(self, dispatcher, tracker, domain):
        # Caricare il dataset
        df = pd.read_csv(DATASET_CHARACTER_PATH)

        # Ottieni razza e classe dagli slot
        selected_race = tracker.get_slot("selected_race")
        selected_class = tracker.get_slot("selected_class")

        # Controlla che entrambi gli slot siano valorizzati
        if not selected_race or not selected_class:
            dispatcher.utter_message(text="Please select both a race and a class to create your character.")
            return []

        # Normalizza la colonna 'race' rimuovendo le parentesi tonde
        df['race'] = df['race'].str.replace(r"[()]", "", regex=True)
        
        # Normalizza la colonna 'race' rimuovendo le parentesi tonde
        df["class_starting"] = df["class_starting"].str.replace(r"[()]", "", regex=True)
        
        # Filtra il dataset per razza e classe
        filtered_df = df[(df["race"] == selected_race) & (df["class_starting"] == selected_class)]
        if not filtered_df.empty:
            # Seleziona un personaggio casuale
            character = filtered_df.sample().iloc[0]

            # Costruire il messaggio del personaggio
            message = (
                f"This is your new Character, built for you based on the choices of Race and Class!\n"
                f"Character {character['race']} {character['class_starting']} created, "
                f"named {character['name']}.\n"
                f"Your level is {character['class_starting_level']}.\n"
                f"Your HP are {character['base_hp']}. - Your health pool\n"
                f"Your initial equipment is {character['inventory']}\nYou have {character['gold']} gold coins.\n"
                f"Your statistics are \nSTR:{character['stats_1']} - Strenght, your physical prowess\nDEX:{character['stats_2']} - Dexterity, your physical agility\n"
                f"CON:{character['stats_3']} - Constituition, your physical health\nINT:{character['stats_4']} - Intelligence, your ability in the studies\n"
                f"WIS:{character['stats_5']} - Wisdom, your ability to understand the world\nCHA:{character['stats_6']} - Charisma, your ability to interact with other beings\n"
            )
            stats_1 = float(character['stats_1'])
            stats_2 = float(character['stats_2'])
            stats_3 = float(character['stats_3'])
            # Verifica se la classe selezionata utilizza incantesimi
            spellcasting_classes = [
                'Warlock', 'Paladin', 'Cleric', 'Wizard', 'Sorcerer',
                'Bard', 'Druid', 'Blood Hunter archived', 'Blood Hunter'
            ]
            if selected_class in spellcasting_classes:
                # Carica il dataset degli incantesimi
                spells_df = pd.read_csv(DATASET_SPELLS_PATH)

                filtered_spells_df = spells_df[spells_df["name"].str.len() <= 25]  # Filtra le spell con nome <= 25 caratteri
                # Seleziona 10 incantesimi casuali e rimuove le parentesi tonde dai nomi
                random_spells = filtered_spells_df.sample(n=10)["name"].str.replace(r"[()]", "", regex=True).tolist()

                # Aggiungi gli incantesimi al messaggio
                spells_message = "\nYour spells are:\n- " + "\n- ".join(random_spells)
                message += spells_message
                spells = random_spells
            else: 
                spells = []
                
            dispatcher.utter_message(text=message)
            # Salva l'inventario e l'oro negli slot
            inventory = character['inventory']

            # Verifica il tipo di inventory
            if isinstance(inventory, float) or pd.isna(inventory):
                # Se è un float (nan o nullo), inizializza una lista vuota
                inventory_list = []
            else:
                # Altrimenti, splitta la stringa
                inventory_list = inventory.split(", ")
            gold = character['gold']
            level = float(character['class_starting_level'])
            
            return [
                SlotSet("level", level), 
                SlotSet("inventory", inventory_list), 
                SlotSet("gold", gold), 
                SlotSet("spells", spells),
                SlotSet("stats_1", stats_1),
                SlotSet("stats_2", stats_2),
                SlotSet("stats_3", stats_3)
            ]
        else:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find any character with race '{selected_race}' and class '{selected_class}'."
            )

        return []
    
class ActionSelectRace(Action):
    def name(self):
        return "action_select_race"

    def run(self, dispatcher, tracker, domain):
        
        dispatcher.utter_message(text=
            f"Now you will be selecting the Race that will stay with you for the rest of the session.\n"
            f"The Race, in this bot, refers to the type of character you are playing.\n"
            f"Each race represents a unique species with specific traits, such as appearance, personality, and special abilities.\n"
            f"Choosing a race will shape your character’s background and interactions in the game world.\n"
            f"For example, you could be an agile Elf, a strong Orc, or a wise Gnome!\n"
            f"You can ask details about the chosen Race later by typing 'Tell me more about the race'. Note that a Race must be chosen first, so better be going and explore them all!\n"
            f"Don’t worry about the rules, just pick the one that you seem to like the most!\n\n"
            )
        # Carica il dataset
        df = pd.read_csv(DATASET_CHARACTER_PATH)
        # Normalizza la colonna 'race' rimuovendo le parentesi tonde
        df['race'] = df['race'].str.replace(r"[()]", "", regex=True)
        # Ottieni una lista di razze uniche
        race_list = df["race"].dropna().unique().tolist()
    
        # Seleziona 4 razze casuali
        random_races = random.sample(race_list, min(len(race_list), 10))

        # Crea i bottoni per le razze
        race_buttons = [
            {"title": race, "payload": f'/select_race{{"selected_race": "{race}"}}'} for race in random_races
        ]

        # Mostra le razze disponibili
        dispatcher.utter_message(text="Select a race from the following options:", buttons=race_buttons, button_type="vertical")
        return []

class ActionSelectClass(Action):
    def name(self):
        return "action_select_class"

    def run(self, dispatcher, tracker, domain):
        # Ottieni la razza selezionata
        selected_race = tracker.get_slot("selected_race")

        if not selected_race:
            dispatcher.utter_message(text="Please select a race first.")
            return []
        
        dispatcher.utter_message(text=
                    f"Now you will be selecting the Class that will stay with you for the rest of the session.\n"
                    f"The Class, in this bot, defines what your character does best during the adventure.\n"
                    f"It represents their role and abilities, such as fighting, casting spells, or supporting the team.\n"
                    f"Each class brings a different playstyle. Note that classes like Artificer, Artificer UA, Monk, Barbarian, Fighter, Rogue and Ranger are considered fighters, so they don't have access to spells. ⚔️\n"
                    f"Instead, classes as Warlock, Paladin, Cleric, Wizard, Sorcerer, Bard, Druid, Blood Hunter and Blood Hunter archived are considered spellcasters, so they have less physical power but they have access to powerful spells. ✨\n"
                    f"You can ask details about the chosen Class later by typing 'Tell me more about the class'. Note that a Class must be chosen first, so better be going and explore them all!\n"
                    f"Choose a class that matches how you want to approach challenges in the game!\n\n"
                    )
        
        # Carica il dataset
        df = pd.read_csv(DATASET_CHARACTER_PATH)
        
        # Normalizza la colonna 'class' rimuovendo le parentesi tonde
        df['race'] = df['race'].str.replace(r"[()]", "", regex=True)
        df['class_starting'] = df['class_starting'].str.replace(r"[()]", "", regex=True)
        
        # Filtra le classi disponibili per la razza selezionata
        class_list = df[df["race"] == selected_race]["class_starting"].dropna().unique().tolist()
        
        if not class_list:
            dispatcher.utter_message(text=f"No classes available for the race '{selected_race}'.")
            return []

        # Seleziona 4 classi casuali
        random_classes = random.sample(class_list, min(len(class_list), 10))

        # Crea i bottoni per le classi
        class_buttons = [
            {"title": class_name, "payload": f'/select_class{{"selected_class": "{class_name}"}}'}
            for class_name in random_classes
        ]

        # Mostra le classi disponibili
        dispatcher.utter_message(text=f"Based on your race '{selected_race}', here are the available classes:", buttons=class_buttons, button_type="vertical")
        return []

class ActionSearchRace(Action):
    def name(self) -> Text:
        return "action_search_race"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Ottieni la razza dallo slot
        race = tracker.get_slot("selected_race")
        if not race:
            dispatcher.utter_message(text="You haven't selected a race. Please choose a race first.")
            return []
    
        # Configura i parametri per la ricerca testuale (descrizione)
        description_params = {
            "q": f"{race} D&D race traits",
            "api_key": SERPAPI_API_KEY
        }

        # Configura i parametri per la ricerca delle immagini
        image_params = {
            "q": f"{race} D&D race traits",
            "tbm": "isch",  # Modalità immagini
            "ijn": 0,       # Prima pagina
            "api_key": SERPAPI_API_KEY
        }

        try:
            # Effettua la ricerca testuale
            description_search = GoogleSearch(description_params)
            description_results = description_search.get_dict()

            # Effettua la ricerca delle immagini
            image_search = GoogleSearch(image_params)
            image_results = image_search.get_dict()

            # Estrarre il primo risultato testuale
            if "organic_results" in description_results and len(description_results["organic_results"]) > 0:
                first_result = description_results["organic_results"][0]
                title = first_result.get("title", "No title available")
                snippet = first_result.get("snippet", "No description available")
                link = first_result.get("link", "No link available")
            else:
                title, snippet, link = None, None, None

            # Estrarre il primo risultato immagine
            if "images_results" in image_results and len(image_results["images_results"]) > 0:
                image_link = image_results["images_results"][0]["original"]
            else:
                image_link = None

            # Costruire la risposta
            response = f"Here's what I found about the {race} race (This could be unappropriate for less known or homebrew races):\n\n"

            if title and snippet:
                response += (
                    f"*{title}*\n"
                    f"Snippet: {snippet}\n"
                    f"More details: {link}\n\n"
                    f"The following image could not be appropriate for less known or homebrew races.\n"
                    f"If the description found before or the image do not satisfy the user, please check the material on the internet for more info. :)"
                )

            if image_link:
                dispatcher.utter_message(text=response, image=image_link)
            else:
                dispatcher.utter_message(text=response)

            if not title and not image_link:
                dispatcher.utter_message(
                    text=f"Sorry, I couldn't find specific information or an image about the {race} race. "
                         f"Try searching on official D&D resources or community guides for more details!"
                )

        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while searching: {str(e)}")

        return []

class ActionSearchClass(Action):
    def name(self) -> Text:
        return "action_search_class"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Ottieni la classe dallo slot
        dnd_class = tracker.get_slot("selected_class")
        if not dnd_class:
            dispatcher.utter_message(text="You haven't selected a class. Please choose a class first.")
            return []

        # Configura i parametri per la ricerca testuale (descrizione)
        description_params = {
            "q": f"{dnd_class} D&D class traits and features",
            "api_key": SERPAPI_API_KEY
        }

        try:
            # Effettua la ricerca testuale
            description_search = GoogleSearch(description_params)
            description_results = description_search.get_dict()

            # Estrarre il primo risultato testuale
            if "organic_results" in description_results and len(description_results["organic_results"]) > 0:
                first_result = description_results["organic_results"][0]
                title = first_result.get("title", "No title available")
                snippet = first_result.get("snippet", "No description available")
                link = first_result.get("link", "No link available")
            else:
                title, snippet, link = None, None, None

            # Costruire la risposta
            response = f"Here's what I found about the {dnd_class} class (This could be unappropriate for homebrew or less known classes):\n\n"

            if title and snippet:
                response += (
                    f"*{title}*\n"
                    f"Snippet: {snippet}\n"
                    f"More details: {link}\n\n"
                    f"If the description does not satisfy the user, please check the official D&D resources. :)"
                )

            
            dispatcher.utter_message(text=response)

        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while searching: {str(e)}")

        return []
    
class ActionCharacterStatus(Action):
    def name(self) -> Text:
        return "action_character_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Recupera i dati dagli slot
        level = tracker.get_slot("level") or "Unknown"
        inventory = tracker.get_slot("inventory") or []
        gold = round(tracker.get_slot("gold"), 1) or 0.0
        spells = tracker.get_slot("spells") or []
        defeat_count = tracker.get_slot("defeat_counter") or 0.0
        # Costruzione del messaggio
        status_message = (
            f"Here is your character's current status:\n\n"
            f"**Level**: {level}\n"
            f"**Gold**: {gold} gold coins\n"
            f"**Number of defeats**: {defeat_count}, don't reach 3 or you'll lose\n\n"
            f"**Inventory**:\n" + 
            (", ".join(inventory) if inventory else "Your inventory is empty.") + "\n\n"
            f"**Spells**:\n" + 
            (", ".join(spells) if spells else "You don't have any spells available.")
        )

        # Invia il messaggio
        dispatcher.utter_message(text=status_message)
        return []

class ActionSpellDetails(Action):
    def name(self) -> Text:
        return "action_spell_details"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Ottieni il testo inserito dall'utente
        user_message = tracker.latest_message.get("text", "").lower()

        # Estrai il nome della spell usando una regex
        match = re.search(r"spell\s+([a-zA-Z\s']+)", user_message)
        if not match:
            dispatcher.utter_message(text="I couldn't extract the spell name from your message. Could you specify it again?")
            return []

        spell_name = match.group(1).strip()

        # Carica il dataset delle spell
        spells_df = pd.read_csv(DATASET_SPELLS_PATH)

        # Rimuove le parentesi tonde dai nomi delle spell nel dataset
        spells_df["normalized_name"] = spells_df["name"].str.replace(r"[()]", "", regex=True).str.strip()

        # Rimuove le parentesi tonde anche dal nome della spell cercata
        normalized_spell_name = re.sub(r"[()]", "", spell_name).strip()

        # Confronta la colonna normalizzata delle spell ignorando il case
        spell_data = spells_df[spells_df["normalized_name"].str.lower() == normalized_spell_name.lower()]

        if spell_data.empty:
            dispatcher.utter_message(text=f"Sorry, I couldn't find any details about the spell '{spell_name}'.")
            return []

        # Recupera i dettagli della spell
        spell_info = spell_data.iloc[0]
        school = spell_info["school"]
        range_ = spell_info["range"]
        duration = spell_info["duration"]
        cast_time = spell_info["cast_time"]

        # Controlla le componenti
        verbal = "Yes" if spell_info["verbal"] == 1 else "No"
        somatic = "Yes" if spell_info["somatic"] == 1 else "No"
        material = "Yes" if spell_info["material"] == 1 else "No"

        # Componenti materiali (se presenti)
        material_cost = spell_info["material_cost"] if pd.notna(spell_info["material_cost"]) else "None"

        # Descrizione generale
        description = spell_info["description"]

        # Costruzione del messaggio
        message = (
            f"Here are the details for the spell '{spell_name}':\n\n"
            f"**School of Magic**: {school}\n"
            f"**Range**: {range_}\n"
            f"**Duration**: {duration}\n"
            f"**Casting Time**: {cast_time}\n\n"
            f"**Components**:\n"
            f"- Verbal: {verbal}\n"
            f"- Somatic: {somatic}\n"
            f"- Material: {material}\n"
        )

        # Aggiunge le componenti materiali se richieste
        if material == "Yes":
            message += f"  - Material Components: {material_cost}\n"

        message += f"\n**Description**:\n{description}"

        # Invia il messaggio
        dispatcher.utter_message(text=message)
        return []
            
class ActionTalkToNPC(Action):
    def name(self) -> Text:
        return "action_talk_to_npc"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        level = tracker.get_slot("level")

        if not level: 
            dispatcher.utter_message(text="Please, go in order and proceed with character creation first.")
            return []

        # Ottieni il nome della città dallo slot
        city_name = tracker.get_slot("selected_city")

        # Carica il dataset
        df = pd.read_csv(DATASET_FAERUN_PATH)

        if city_name:
            # Cerca i dettagli della città selezionata nel dataset
            city_data = df[df["Nation or City-State"].str.lower() == city_name.lower()]
            
            if city_data.empty:
                # Se la città nello slot non è valida, scegline una nuova
                selected_city = df.sample().iloc[0]
                city_name = selected_city["Nation or City-State"]
                dispatcher.utter_message(text=f"The city '{tracker.get_slot('selected_city')}' could not be found. You have been redirected to {city_name}.")
            else:
                # Usa la città esistente
                selected_city = city_data.iloc[0]
                dispatcher.utter_message(text=f"You are still in {city_name}. Let’s continue exploring.")
        else:
            # Se lo slot è vuoto, seleziona una città casuale
            selected_city = df.sample().iloc[0]
            city_name = selected_city["Nation or City-State"]


        # Simula il 50% di probabilità di incontrare un NPC normale o un mercante
        npc_type = random.choice(["normal", "merchant"])
  

        if npc_type == "normal":
            # Estrarre informazioni sulla città
            region = selected_city["Region"]
            government = selected_city["Government"]
            religion = selected_city["Religion"] if not pd.isna(selected_city["Religion"]) else "no particular religion"
            leader = selected_city["Leader"] if not pd.isna(selected_city["Leader"]) else "an unknown ruler"
            primary_race = selected_city["Primary Race"]
            secondary_race = selected_city["Secondary Race"] if not pd.isna(selected_city["Secondary Race"]) else "various races"
            opposed_to = selected_city["Opposed To"] if not pd.isna(selected_city["Opposed To"]) else "some dangerous figures from other cities that could be here"
            notes = selected_city["Notes"] if not pd.isna(selected_city["Notes"]) else "it is a place of mystery :D"

            # Seleziona una descrizione casuale
            specific_descriptions = [
                f"In {city_name}, the {primary_race} community is thriving, but tensions with {opposed_to} sometimes arise.",
                f"{city_name} is a bustling city, well known for {notes}.",
                f"The streets of {city_name} are lively, with a mix of {primary_race} and {secondary_race}.",
                f"In {city_name}, {leader} ensures order while the {government} maintains balance.",
                f"{city_name} is famous for its {religion} traditions and its unique culture."
            ]

            selected_description = random.choice(specific_descriptions)
            await asyncio.sleep(0.1)  
            dispatcher.utter_message(text=f"You have arrived in {city_name}.\nYou meet a friendly villager.\nHe says: {selected_description}")

            # Bottoni per continuare o tornare al menu
            buttons = [
                {"title": "Continue talking", "payload": "/continue_talking"},
                {"title": "Return to menu", "payload": "/return_to_post_creation"},
            ]

            await asyncio.sleep(0.1)
            dispatcher.utter_message(text="What would you like to do next?", buttons=buttons, button_type="vertical")
        
        if npc_type == "merchant":
            # Carica il dataset e seleziona 20 oggetti casuali
            df = pd.read_csv(DATASET_EQUIPS_PATH)
            sampled_items = df.sample(n=20)

            item_list = []
            for idx, (_, row) in enumerate(sampled_items.iterrows(), start=1):
                item_name = row["Name"]
                item_cost = row["Price (golds)"]
                clean_item_name = item_name.replace("(", "").replace(")", "").strip()
                if pd.isna(item_cost):
                    item_cost = round(random.uniform(1.0, 10.0), 1)
                item_list.append({"index": idx, "name": clean_item_name, "cost": item_cost})
            button = [
                {"title": "Return to menu", "payload": "/return_to_post_creation"},
            ]
            # Salva gli oggetti del mercante come slot
            dispatcher.utter_message(
                text=f"The merchant shows you their wares. Type the number of the item you wish to buy:\n\n" +
                     "\n".join([f"{item['index']}: {item['name']} ({item['cost']} gold)" for item in item_list]), buttons=button, button_type="vertical"
            )

            return [SlotSet("merchant_items", item_list), SlotSet("selected_city", city_name)]

        # Assicurati che la città sia memorizzata nello slot solo la prima volta
        return [SlotSet("selected_city", city_name)]


class ActionSelectItem(Action):
    def name(self) -> Text:
        return "action_select_item"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        merchant_items = tracker.get_slot("merchant_items") or []
        inventory = tracker.get_slot("inventory") or []
        gold = tracker.get_slot("gold") or 0
        level = tracker.get_slot("level")
        
        if not merchant_items or not level: 
            dispatcher.utter_message(text="Please, go in order and proceed with character creation first")
            return[]
        
        # Ottieni il messaggio dell'utente
        user_message = tracker.latest_message.get("text", "").strip().lower()
        button = [
                {"title": "Return to menu", "payload": "/return_to_post_creation"},
            ]
        
        # Controlla se l'input è un numero valido
        if not user_message.isdigit():
            dispatcher.utter_message(text="Invalid input. Please type the number of the item you want to buy.", buttons = button, button_type="vertical")
            return []
        
        item_index = int(user_message)

        # Controlla se il numero selezionato è valido
        selected_item = next((item for item in merchant_items if item["index"] == item_index), None)
        
        if not selected_item:
            dispatcher.utter_message(text="Invalid selection. Please choose a number from the list. ", buttons = button, button_type="vertical")
            return []

        item_name = selected_item["name"]
        item_cost = selected_item["cost"]

        # Controlla se l'utente ha abbastanza oro
        if gold < item_cost:
            dispatcher.utter_message(text=f"You don't have enough gold to buy {item_name}. You have {round(gold, 1)} gold left.\nType another number to buy an item or press the button below to go back.", buttons = button, button_type="vertical")
            return []

        # Rimuovi l'oggetto dalla lista del mercante
        updated_items = [item for item in merchant_items if item["index"] != item_index]

        # Aggiungi l'oggetto all'inventario
        inventory.append(item_name)
        gold -= item_cost

        dispatcher.utter_message(
            text=f"You have purchased {item_name} for {item_cost} gold. You have {round(gold,1)} gold left."
        )
        
        # Mostra la lista aggiornata se ci sono ancora oggetti
        if updated_items:
            dispatcher.utter_message(
                text="Here are the remaining items. Type the number to buy:\n\n" +
                     "\n".join([f"{item['index']}: {item['name']} ({item['cost']} gold)" for item in updated_items]), buttons=button, button_type="vertical"
            )
        else:
            dispatcher.utter_message(text="The merchant has no more items to sell.")

        # Salva l'inventario e l'oro aggiornati
        return [SlotSet("merchant_items", updated_items), SlotSet("inventory", inventory), SlotSet("gold", gold)]


class ActionContinueTalking(Action):
    def name(self) -> Text:
        return "action_continue_talking"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        level = tracker.get_slot("level")

        if not level: 
            dispatcher.utter_message(text="Please, go in order and proceed with character creation first")
            return[]
        
        city_name = tracker.get_slot("selected_city")
        
        if not city_name:
            dispatcher.utter_message(text="I seem to have forgotten which city we're in. Please go back and talk to an NPC again.")
            return []
        
        # Descrizioni generiche per il dialogo
        general_descriptions = [
            "The crops this year have been plentiful, thanks to the recent rains.",
            "They say the blacksmith's daughter can craft the finest swords in the region.",
            "I've heard strange noises coming from the old ruins just outside of town.",
            "Merchants from the south bring the most exotic spices—you should try some.",
            "There's a bard in the tavern who knows tales that will give you chills.",
            "The mayor is organizing a festival next week. You’ll see colorful parades and music all day long.",
            "A local farmer’s cow gave birth to a calf with strange markings. People say it’s a good omen.",
            "The town healer has discovered a new herbal remedy for fevers. Everyone’s talking about it.",
            "The moonlight reflecting off the city’s canals is a sight to behold tonight.",
            "The city guards have been patrolling more often recently. I wonder what’s going on.",
            "A merchant in the market square is selling rare gems from distant lands.",
            "There’s a hidden garden in the eastern district that only a few locals know about.",
            "The old storyteller by the fountain knows legends about dragons and ancient wars.",
            "You can smell the bakery from here. Their cinnamon pastries are simply divine.",
            "The temple bells are ringing earlier than usual today. It must be a special occasion.",
            "The forest nearby is said to be cursed, but some brave hunters still venture there.",
            "You should visit the artisan district if you’re interested in handcrafted jewelry.",
            "The harbor has been unusually busy lately. Perhaps a fleet of ships arrived overnight.",
            "I once saw a shooting star over the hills beyond the city walls. It was magical.",
            "The cobbler down the road claims he can make shoes that never wear out.",
            "A bard composed a song about our city, and it’s quickly becoming a local favorite.",
            "Many travelers stop by the old library to read the scrolls written by ancient scholars.",
            "The miller’s son is training to be a knight. He dreams of serving the king someday.",
            "There’s an underground tunnel system beneath the city, but few dare to explore it.",
            "I once witnessed a duel between two knights in the city square. It was unforgettable.",
            "A strange caravan arrived yesterday carrying spices, silk, and mysterious artifacts.",
            "The herbalist has started experimenting with rare plants from the nearby forest.",
            "I remember the last time we had a storm like this. The river almost flooded the town.",
            "The butcher has been working on a new sausage recipe, and the locals love it.",
            "An old tower on the outskirts of town is said to be haunted by a restless spirit.",
            "The tailor is making a special cloak for the town’s champion. It’s said to bring good fortune.",
            "A traveler once told me about a magical spring in the mountains that grants wishes.",
            "The blacksmith’s forge never seems to rest, always glowing with the heat of molten metal.",
            "Some fishermen believe the lake monster is real, but no one has seen it in years.",
            "The jeweler recently acquired a gemstone that supposedly brings good luck to its wearer.",
            "If you ever need a guide, the tavern is the best place to find experienced adventurers.",
            "The city gates are impressive, aren’t they? They were built centuries ago to repel invaders.",
            "We used to see more adventurers pass through this town. It’s quieter now than it once was.",
            "There’s a mysterious old man who lives in the abandoned cottage near the forest.",
            "A hidden cove by the cliffs is said to be the hiding place of pirates long forgotten."
        ]
       # Scegli una descrizione generica casuale
        description = random.choice(general_descriptions)

        # Messaggio con la descrizione
        dispatcher.utter_message(text=f"The villager continues: '{description}'")

        # Bottoni per continuare a parlare o tornare al menu
        buttons = [
            {"title": "Continue talking", "payload": "/continue_talking"},
            {"title": "Return to menu", "payload": "/return_to_post_creation"},
        ]
        
        await asyncio.sleep(0.1)
        dispatcher.utter_message(text="What would you like to do next?", buttons=buttons, button_type="vertical")

        return []

class ActionExploreCity(Action):
    def name(self) -> Text:
        return "action_explore_city"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        level = tracker.get_slot("level")

        if not level: 
            dispatcher.utter_message(text="Please, go in order and proceed with character creation first")
            return[]
        
        # Lista delle descrizioni generali della città
        city_name = tracker.get_slot("selected_city")
        if city_name:
            # Se la città è già selezionata, usa quella esistente
            dispatcher.utter_message(text=f"You are still in {city_name}. ")
            
            general_descriptions = [
            f"the people of {city_name} are known for their hospitality.",
            f"in {city_name}, the market square is always bustling with activity.",
            f"you hear local tales about the origins of {city_name}, dating back centuries.",
            f"the architecture in {city_name} reflects its rich cultural history.",
            f"a local baker in {city_name} is famous for making pastries with exotic spices.",
            f"the city guards of {city_name} patrol the streets, ensuring peace and order.",
            f"in the distance, you see the grand palace of {city_name}, a symbol of its prosperity.",
            f"the port of {city_name} is busy with merchants from distant lands.",
            f"the people in {city_name} celebrate their annual harvest festival with music and dance.",
            f"the old library in {city_name} contains scrolls and tomes of forgotten knowledge.",
            f"the smell of roasted meats and spiced wine drifts from a tavern near the gates of {city_name}.",
            f"a peaceful garden sanctuary in {city_name} offers rest and quiet for travelers and locals alike.",
            f"an ancient statue of a forgotten deity stands at the center of {city_name}, shrouded in mystery.",
            f"locals in {city_name} enjoy evening walks along the river, watching the sun set behind the hills.",
            f"the city of {city_name} is known for its colorful street festivals, where merchants and performers take to the streets.",
            f"the cobblestone streets of {city_name} echo with the chatter of merchants and the laughter of children.",
            f"a stone bridge spans the river running through {city_name}, its arches adorned with carvings of mythical creatures.",
            f"the annual lantern festival in {city_name} lights up the night as paper lanterns float gently into the sky.",
            f"the aroma of freshly brewed ale drifts from a local brewery in {city_name}, famous for its strong drinks.",
            f"fountains with statues of legendary heroes decorate public parks throughout {city_name}, telling stories of past victories."
            f"The narrow alleys of {city_name} twist and turn, revealing hidden shops and cozy cafes.",
            f"In {city_name}, street performers captivate crowds with music, acrobatics, and magic tricks.",
            f"A gentle breeze carries the scent of blooming flowers from the gardens of {city_name}.",
            f"The bustling market of {city_name} offers everything from rare spices to enchanted trinkets.",
            f"Children chase each other through the squares of {city_name}, their laughter echoing off the stone walls.",
            f"The temple bells of {city_name} chime, calling worshippers to prayer.",
            f"In {city_name}, artisans can be seen carefully crafting intricate jewelry and pottery.",
            f"The town crier stands in the center of {city_name}, sharing the latest news and announcements.",
            f"A famous blacksmith in {city_name} is known for crafting weapons used by the king’s knights.",
            f"The scent of fresh bread wafts through the streets as bakers in {city_name} prepare their daily goods.",
            f"The harbor of {city_name} is alive with activity as sailors sing shanties while loading their ships.",
            f"Ancient ruins on the outskirts of {city_name} draw scholars seeking lost knowledge.",
            f"At night, the lantern-lit streets of {city_name} create a peaceful glow as couples stroll through town.",
            f"A street vendor in {city_name} offers roasted chestnuts and sweet pastries to passersby.",
            f"The grand amphitheater of {city_name} hosts performances that attract audiences from distant lands.",
            f"Local fishermen in {city_name} haul in their morning catch, selling fresh seafood to eager customers.",
            f"The central plaza of {city_name} is adorned with colorful banners and bustling merchants.",
            f"A group of storytellers gathers around a fire in {city_name}, sharing epic tales of adventure.",
            f"The sound of hammers echoes from the forges in {city_name}, where blacksmiths craft weapons and armor.",
            f"The towering clock tower of {city_name} serves as a landmark visible from every corner of the city.",
            f"The main avenue of {city_name} is lined with flowering trees, providing shade for pedestrians.",
            f"Local farmers arrive at the market in {city_name} with carts full of fresh produce and dairy.",
            f"In the heart of {city_name}, you find a fountain carved with scenes of ancient battles.",
            f"The library of {city_name} houses maps and scrolls that chart forgotten territories and ancient realms.",
            f"A bustling inn in {city_name} is filled with adventurers exchanging stories of their travels.",
            f"A well-known herbalist in {city_name} prepares potions and remedies from rare plants gathered nearby.",
            f"The aroma of grilled meats fills the streets during the midday meal as vendors serve hungry citizens.",
            f"The mayor’s mansion in {city_name} stands tall, a symbol of political power and wealth.",
            f"The sound of wind chimes hangs in the air as the breeze passes through the narrow alleys of {city_name}.",
            f"A group of performers in {city_name} juggles flaming torches, drawing cheers from onlookers."
            ]

            # Scegli una descrizione casuale
            description = random.choice(general_descriptions)

            await asyncio.sleep(0.1)  # Pausa per un'esperienza naturale
            dispatcher.utter_message(text=f"While exploring {city_name} you discover that {description}")

            # Bottoni per continuare o tornare al menu
            buttons = [
                {"title": "Continue exploring", "payload": "/explore_city"},
                {"title": "Return to menu", "payload": "/return_to_post_creation"},
            ]

            await asyncio.sleep(0.1)
            dispatcher.utter_message(text="What would you like to do next?", buttons=buttons, button_type="vertical")

            return []
        else:
            dispatcher.utter_message(text=f"You feel that this is a strange city, you don't know much about it. Maybe it would be better to talk to someone first")
            # Bottoni per continuare o tornare al menu
            buttons = [
                {"title": "Return to menu", "payload": "/return_to_post_creation"},
            ]

            await asyncio.sleep(0.1)
            dispatcher.utter_message(text="What would you like to do next (Hint: Talk to an NPC first)?", buttons=buttons, button_type="vertical")

            return []
            
class ActionAskForCustomInput(Action):
    def name(self) -> Text:
        return "action_ask_for_custom_input"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Type your next action (write /help for the available commands).")
        return []
    
class ActionStartCombat(Action):
    def name(self) -> Text:
        return "action_start_combat"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        player_level = tracker.get_slot("level")
        selected_class = tracker.get_slot("selected_class")
        strength = tracker.get_slot("stats_1") or 0
        dexterity = tracker.get_slot("stats_2") or 0
        constitution = tracker.get_slot("stats_3") or 0
        
        if player_level is None:
            dispatcher.utter_message(text="I need to know your level before we start the combat. Return to character creation first!")
            return []

        # Carica il dataset dei mostri
        monsters_df = pd.read_csv(DATASET_MONSTER_FILTERED)

        # Seleziona casualmente un mostro
        selected_monster_data = monsters_df.sample(n=1).iloc[0]
        selected_monster = selected_monster_data["name"]
        try:
            monster_cr = float(Fraction(selected_monster_data["cr"]))
        except ValueError:
            dispatcher.utter_message(text=f"Error: Unable to process CR '{selected_monster_data['cr']}'.")
            return []

        difficulty_message = ""
        combat_difficulty = 0.0

        # Determina la difficoltà del combattimento
        difficulty_difference = monster_cr - player_level

        if difficulty_difference < 1.0:
            difficulty_message = f"The fight against {selected_monster} is extremely easy, you could beat this anytime. Continue?"
            combat_difficulty = 1.0
        elif 1.0 <= difficulty_difference < 3.0:
            difficulty_message = f"The fight against {selected_monster} is difficult but possible, continue fighting?"
            combat_difficulty = 5.0
        elif 3.0 <= difficulty_difference < 5.0:
            difficulty_message = f"The fight against {selected_monster} is pretty difficult, could be a close one. Continue?"
            combat_difficulty = 10.0
        elif difficulty_difference >= 5.0:
            difficulty_message = f"The fight against {selected_monster} is extremely difficult, high probabilities to die. Continue anyway?"
            combat_difficulty = 15.0
        
        # Calcola la somma delle statistiche fisiche se il giocatore non è uno spellcaster
        non_spellcaster_classes = ['Artificier', 'Artificier UA', 'Fighter', 'Barbarian', 'Rogue', 'Monk', 'Ranger']
        
        if selected_class in non_spellcaster_classes:
            physical_stat_sum = strength + dexterity + constitution

            if physical_stat_sum >= 35.0:
                combat_difficulty -= 3.0  # Riduce la difficoltà
                
                
                
        # Bottoni di scelta
        buttons = [
            {"title": "Continue fighting", "payload": "/continue_fighting"},
            {"title": "Cast a spell", "payload": "/cast_spell"},
            {"title": "Run away", "payload": "/return_to_post_creation"},
        ]
        
        # Mostra il messaggio della difficoltà e i bottoni di scelta
        dispatcher.utter_message(text=f"Given your strenght, the difficulty has been reduced to {combat_difficulty}. {difficulty_message}", buttons=buttons, button_type="vertical")

        # Imposta lo slot del mostro selezionato e la difficoltà
        return [SlotSet("combat_difficulty", combat_difficulty)]

class ActionContinueFighting(Action):
    def name(self) -> Text:
        return "action_continue_fighting"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        difficulty = tracker.get_slot("combat_difficulty")
        defeat_counter = tracker.get_slot("defeat_counter") or 0
        player_level = tracker.get_slot("level")
        
        if player_level is None:
            dispatcher.utter_message(text="I need to know your level before we start the combat. Return to character creation first!")
            return []
        
        # Estrazione di un numero casuale tra 1 e 20
        roll = random.randint(1, 20)
        dispatcher.utter_message(text=f"You rolled a {roll}. The required difficulty is {max(1, difficulty)}.")

        # Verifica se il combattimento è vinto o perso
        if roll >= difficulty:
            # Determina la ricompensa basata sulla difficoltà
            if difficulty <= 1.0:
                gold_reward = 50.0
                # Bottoni di scelta
                buttons = [
                {"title": "Return to city", "payload": "/return_to_post_creation"},
                ]
        
                # Mostra il messaggio della difficoltà e i bottoni di scelta
                dispatcher.utter_message(f"You won the battle and earned {gold_reward} gold coins.", buttons=buttons, button_type="vertical")
            
                return [SlotSet("gold", tracker.get_slot("gold") + gold_reward), SlotSet("remaining_spells", None)]
            elif 1.0 < difficulty <= 5.0:
                gold_reward = 100.0

                # Bottoni di scelta
                buttons = [
                {"title": "Return to city", "payload": "/return_to_post_creation"},
                ]
        
                # Mostra il messaggio della difficoltà e i bottoni di scelta
                dispatcher.utter_message(f"You won the battle and earned {gold_reward} gold coins.", buttons=buttons, button_type="vertical")
            
                return [SlotSet("gold", tracker.get_slot("gold") + gold_reward), SlotSet("remaining_spells", None)]
            elif 5.0 < difficulty <= 10.0:
                gold_reward = 500.0
                # Bottoni di scelta
                buttons = [
                {"title": "Return to city", "payload": "/return_to_post_creation"},
                ]
        
                # Mostra il messaggio della difficoltà e i bottoni di scelta
                dispatcher.utter_message(f"You won the battle and earned {gold_reward} gold coins.", buttons=buttons, button_type="vertical")
            
                return [SlotSet("gold", tracker.get_slot("gold") + gold_reward),SlotSet("remaining_spells", None)]
            elif 10.0 < difficulty <= 15.0:
                gold_reward = 1000.0
                # Bottoni di scelta
                buttons = [
                {"title": "Return to city", "payload": "/return_to_post_creation"},
                
                ]
        
                # Mostra il messaggio della difficoltà e i bottoni di scelta
                dispatcher.utter_message(f"You won the battle and earned {gold_reward} gold coins.", buttons=buttons, button_type="vertical")

                return [SlotSet("gold", tracker.get_slot("gold") + gold_reward), SlotSet("remaining_spells", None)]            
        else:
            # Incrementa il contatore delle sconfitte
            defeat_counter += 1.0
            
            # Bottoni di scelta
            buttons = [
            {"title": "Return to city", "payload": "/return_to_post_creation"},
            ]
        
            # Mostra il messaggio della difficoltà e i bottoni di scelta
            dispatcher.utter_message("You lost the battle.", buttons=buttons, button_type="vertical")
                
            # Controlla se il contatore delle sconfitte è pari a 3
            if defeat_counter == 3.0:
                dispatcher.utter_message(text="You have lost 3 battles. Your character has died. Resetting character...")
                return [AllSlotsReset()]

            return [SlotSet("defeat_counter", defeat_counter), SlotSet("remaining_spells", None)]

class ActionCastSpell(Action):
    def name(self) -> Text:
        return "action_cast_spell"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        spells = tracker.get_slot("spells") or []
        remaining_spells = tracker.get_slot("remaining_spells") or spells.copy()
        player_level = tracker.get_slot("level")  
              
        if player_level is None:
            dispatcher.utter_message(text="I need to know your level before we start the combat. Return to character creation first!")
            return []
        
        if not remaining_spells:
            buttons = [
                {"title": "Continue fighting", "payload": "/continue_fighting"},
                {"title": "Run away", "payload": "/return_to_post_creation"}
            ]
            dispatcher.utter_message(text="You don't have any spells to cast. What do you want to do?", buttons=buttons, button_type="vertical")
            return []

        # Limita la lunghezza dei nomi e rimuove caratteri problematici
        def clean_spell_name(spell):
            cleaned_spell = re.sub(r'[^\w\s]', '', spell)  # Rimuove caratteri speciali
            return cleaned_spell[:25]  # Taglia il nome a max 30 caratteri

        # Crea bottoni con un ID univoco per ogni spell
        spell_buttons = [
            {
                "title": clean_spell_name(spell),
                "payload": f'/select_spell{{"selected_spell": "{clean_spell_name(spell)}"}}'
            }
            for spell in remaining_spells
        ]

        spell_buttons.append({"title": "Write your action (/help for commands)", "payload": "/custom_input_prompt"})

        dispatcher.utter_message(text="Select a spell to cast:", buttons=spell_buttons, button_type="vertical")
        return []
        
class ActionProcessSpell(Action):
    def name(self) -> Text:
        return "action_process_spell"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        spells = tracker.get_slot("spells") or []
        difficulty = tracker.get_slot("combat_difficulty")
        remaining_spells = tracker.get_slot("remaining_spells") or spells.copy()

        selected_spell = tracker.get_slot("selected_spell")

        if len(remaining_spells) < 8:
            buttons = [
                {"title": "Continue fighting", "payload": "/continue_fighting"},
                {"title": "Run away", "payload": "/return_to_post_creation"},
            ]
            dispatcher.utter_message(text = f"You have consumed all your magic energies. No more spells can be cast. The difficulty is now {difficulty}. What do you want to do?", buttons=buttons, button_type="vertical")
            return [SlotSet("remaining_spells", None)]

        # Se l'incantesimo selezionato non è valido
        if not selected_spell or selected_spell not in remaining_spells:
            buttons = [
                {"title": "Continue fighting", "payload": "/continue_fighting"},
                {"title": "Cast a spell", "payload": "/cast_spell"},
                {"title": "Run away", "payload": "/return_to_post_creation"},
            ]
            dispatcher.utter_message(text = "Invalid spell selected or the spell is no longer available.", buttons=buttons, button_type="vertical")
            return []

        # Rimuove la spell dalla lista temporanea e aggiorna la difficoltà
        dispatcher.utter_message(text=f"You cast {selected_spell}. The difficulty decreases by 1.")
        remaining_spells.remove(selected_spell)

        # Se ci sono altre spell disponibili, mostra i bottoni aggiornati
        if remaining_spells:
            spell_buttons = [
                {"title": spell, "payload": f'/select_spell{{"selected_spell": "{spell}"}}'}
                for spell in remaining_spells
            ]
            spell_buttons.append({"title": "Write your action (/help for commands)", "payload": "/custom_input_prompt"})
            dispatcher.utter_message(text="Select another spell or return to the fight:", buttons=spell_buttons, button_type="vertical")
        else:
            buttons = [
                {"title": "Continue fighting", "payload": "/continue_fighting"},
                {"title": "Run away", "payload": "/return_to_post_creation"},
            ]
            dispatcher.utter_message(text ="No spells left to cast. You must continue fighting.", buttons=buttons, button_type="vertical")

        return [
            SlotSet("combat_difficulty", max(1, difficulty - 1)),
            SlotSet("remaining_spells", remaining_spells)
        ]
        
class ActionHelp(Action):
    def name(self) -> Text:
        return "action_help"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        help_message = (
            "**Available Commands:**\n\n"
            "1. **Describe monster** (You have to imput the monster name):\n"
            "   - Example: *Tell me about the monster Zombie* (For improved performance is best to fight some monsters first!)\n"
            "   - Will give a description of the monster called by the name.\n\n"
            
            "2. **Get monster stats** (You have to imput the monster name):\n"
            "   - Example: *What are the stats of the monster Zombie* (For improved performance is best to fight some monsters first!)\n"
            "   - Will give a description of how strong the monster is by explaining its statistics.\n\n"
            
            "3. **Ask about race**:\n"
            "   - Example: *Tell me about this race* (can be called after character creation)\n"
            "   - Will give a description of the race chosen during character creation.\n\n"
            
            "4. **Ask about class**:\n"
            "   - Example: *Tell me about this class* (can be called after character creation)\n"
            "   - Will give a description of the class chosen during character creation.\n\n"
            
            "5. **Character status**:\n"
            "   - Example: *Show me my character status* (can be called after character creation)\n"
            "   - Will give a summary of the current character status.\n\n"
            
            "6. **Spell details**:\n"
            "   - Example: *Tell me about the spell Fireball*\n"
            "   - Will give a general description of the spell as it would be in a D&D manual.\n\n"
            
            "8. **Cast Spell** (Only in combat):\n"
            "   - Example: */cast_spell*, *Cast Spell*\n"
            "   - If you are in combat and you exited to see the description of a spell, you can return to spells menu by typing this command\n"
            
            "7. **Return to main menu**:\n"
            "   - Example: *Return to main menu* (can be called after character creation)\n"
            "   - Will bring you back to the selection of actions that can be done in an adventure.\n\n"
            
            "8. **Reset**:\n"
            "   - Example: *Reset*, *Cancel operation*\n"
            "   - Will reset everything and restart the session completely.\n"
            
            "8. **Play**:\n"
            "   - Example: */Play*, *Let's play*\n"
            "   - Will start a new session, beginning with character creation (ADVISE - Do this command if it's the first time running the bot, later on will overwrite the saved character data).\n"
        )

        dispatcher.utter_message(text=help_message)
        return []        