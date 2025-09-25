# --- File Paths --- #
COMMANDER_IMG_PATH = "commander.png"
COMMANDER_FRONT_IMG_PATH = "commander_front.png"
COMMANDER_BACK_IMG_PATH = "commander_back.png"
PARTNER_IMG_PATH = "partner.png"
DEBUG_SCREENSHOT_PATH_TPL = "debug_screenshot_{site}.png"
DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH = "debug_screenshot_unexpected_error.png"

# --- API and URLs --- #
SCRYFALL_API_BASE_URL = "https://api.scryfall.com"
SCRYFALL_API_CARD_SEARCH_URL = f"{SCRYFALL_API_BASE_URL}/cards/search"
SCRYFALL_API_CARD_RANDOM_URL = f"{SCRYFALL_API_BASE_URL}/cards/random"
SCRYFALL_SYNTAX_GUIDE_URL = "https://scryfall.com/docs/syntax"
EDHREC_PARTNERS_URL_TPL = "https://edhrec.com/partners/{slug}"
EDHREC_DECKS_URL_TPL = "https://edhrec.com/decks/{slug}"
EDHREC_DECK_PREVIEW_URL_TPL = "https://edhrec.com/deckpreview/{hash}"

# --- Headers --- #
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Accept": "application/json;q=0.9,*/*;q=0.8"
}

# --- EDHRec Tags --- #
EDHREC_TAGS = [
    "+1/+1 Counters", "Ad Nauseam", "Advisors", "Adventure", "Adventures", "Affinity", "Aggro", "Aikido",
    "Allies", "Amass", "Angels", "Anthems", "Apes", "Arcane", "Archers", "Aristocrats", "Artificers",
    "Artifacts", "Assassins", "Astartes", "Atogs", "Attack Triggers", "Attractions", "Auras", "Avatars",
    "Banding", "Bant", "Barbarians", "Bears", "Beasts", "Big Mana", "Birds", "Birthing Pod",
    "Blink", "Blood", "Blue Moon", "Boros", "Bounce", "Budget", "Burn", "Cantrips", "Card Draw",
    "Cascade", "Cats", "Caves", "cEDH", "Cephalids", "Chaos", "Charge Counters", "Cheerios", "Clerics",
    "Clones", "Clues", "Coin Flip", "Color Hack", "Colorless", "Combo", "Commander Matters", "Companions",
    "Conspicuous", "Constructs", "Control", "Convoke", "Counters", "Crabs", "Craft", "Creatureless",
    "Crime", "Curses", "Cybermen", "Cycling", "Daleks", "Dandan", "Day / Night", "Deathtouch", "Defenders",
    "Delirium", "Delver", "Demons", "Descend", "Deserts", "Detectives", "Devils", "Devotion", "Die Roll",
    "Dimir", "Dinosaurs", "Discard", "Discover", "Dogs", "Dolmen Gate", "Donate", "Dredge", "Drakes",
    "Dragon's Approach", "Dragons", "Druids", "Dune-Brood", "Dungeon", "Dwarves", "Eggs", "Elders",
    "Eldrazi", "Elementals", "Elephants", "Elves", "Enchantress", "Energy", "Enrage", "Equipment", "Esper",
    "ETB", "Evoke", "Exalted", "Exile", "Experience Counters", "Exploit", "Explore", "Extra Combats",
    "Extra Turns", "Faeries", "Fight", "Finisher", "Five-Color", "Flash", "Flashback",
    "Fling", "Flying", "Food", "Forced Combat", "Foretell", "Foxes", "Freerunning", "Frogs", "Fungi",
    "Gaea's Cradle", "Giants", "Glint-Eye", "Gnomes", "Goblins", "Gods", "Golems", "Golgari", "Good Stuff",
    "Gorgons", "Graveyard", "Griffins", "Grixis", "Group Hug", "Group Slug", "Gruul", "Guildgates",
    "Gyruda Companion", "Halflings", "Hand Size", "Hare Apparent", "Haste", "Hatebears", "Hellbent",
    "Heroic", "High Power", "Hippos", "Historic", "Horrors", "Horses", "Humans", "Hydras", "Illusions",
    "Impulse Draw", "Improvise", "Infect", "Ink-Treader", "Insects", "Izzet", "Jegantha Companion",
    "Jeskai", "Jund", "Kaheera Companion", "Keruga Companion", "Keywords", "Kicker", "Kindred", "Kithkin",
    "Knights", "Kor", "Land Animation", "Land Destruction", "Landfall", "Lands Matter", "Landwalk",
    "Legends", "Lhurgoyfs", "Life Exchange", "Lifedrain", "Lifegain", "Lizards", "Lurrus Companion",
    "Lure", "Madness", "Mardu", "Mercenaries", "Merfolk", "Mice", "Midrange", "Mill", "Minions",
    "Minotaurs", "Modular", "Monarch", "Monkeys", "Monks", "Mono-Black", "Mono-Blue", "Mono-Green",
    "Mono-Red", "Mono-White", "Morph", "Mount", "Multicolor Matters", "Mutants", "Mutate", "Myr",
    "Myriad", "Naya", "Necrons", "Nightmares", "Ninjas", "Ninjutsu", "Obosh Companion", "Offspring",
    "Ogres", "Oil Counters", "Old School", "Oozes", "Orcs", "Orzhov", "Otters", "Outlaws", "Paradox",
    "Party", "Persistent Petitioners", "Phasing", "Phoenixes", "Phyrexians", "Pillow Fort", "Pingers",
    "Pirates", "Planeswalkers", "Plants", "Politics", "Polymorph", "Populate", "Power", "Praetors",
    "Primal Surge", "Prison", "Proliferate", "Prowess", "Rabbits", "Raccoons", "Rad Counters",
    "Rakdos", "Ramp", "Rat Colony", "Rats", "Reach", "Reanimator", "Rebels", "Relentless Rats", "Robots",
    "Rock", "Rogues", "Rooms", "Saboteurs", "Sacrifice", "Sagas", "Samurai", "Saprolings", "Satyrs",
    "Scarecrows", "Scry", "Sea Creatures", "Selesnya", "Self-Damage", "Self-Discard", "Self-Mill",
    "Servos", "Shades", "Shadowborn Apostles", "Shamans", "Shapeshifters", "Sharks", "Shrines", "Simic",
    "Skeletons", "Skulk", "Slivers", "Slime Against Humanity", "Snakes", "Sneak Attack", "Snow",
    "Soldiers", "Specters", "Spell Copy", "Spellslinger", "Sphinxes", "Spiders", "Spirits",
    "Spore Counters", "Squad", "Squirrels", "Stax", "Stickers", "Stompy", "Stoneblade", "Storm",
    "Sultai", "Sunforger", "Superfriends", "Surveil", "Suspend", "Tap / Untap", "Temur", "Tempo",
    "Tempest Hawk", "Templar Knights", "The Ring", "Theft", "Thopters", "Time Counters", "Time Lords",
    "Tokens", "Toolbox", "Topdeck", "Toughness Matters", "Treasure", "Treefolk", "Triggered Abilities",
    "Tron", "Turbo Fog", "Turtles", "Tyranids", "Type Hack", "Umori Companion", "Unblockable", "Unicorns",
    "Unnatural", "Vampires", "Vanilla", "Vehicles", "Villainous Choice", "Voltron", "Voting", "Warriors",
    "Weenies", "Werewolves", "Whales", "Wheels", "Witch-Maw", "Wizards", "Wolves", "Wraiths", "Wurms",
    "X Spells", "Yore-Tiller", "Zirda Companion", "Zombies", "Zoo"
]