import discord
import os
from discord.ext import commands
from discord import app_commands
import random
from keep_alive import keep_alive
from hero_data import FRAG_HEROES, COUNTER_MAP # This imports the hero data from hero_data.py

# --- Configuration ---
# Set the command prefix (what users type before a command, e.g., !hero_stats)
intents = discord.Intents.default()
intents.message_content = True # Required to read messages for commands
bot = commands.Bot(command_prefix='!', intents=intents)

# --- New Code Block: Sync Slash Commands ---

keep_alive()
# IMPORTANT: Restart your bot every time you make changes to the command structure.

# 🛑 CRITICAL: REPLACE THIS WITH YOUR ACTUAL BOT TOKEN!
bot.run(os.environ['DISCORD_TOKEN']) 

# --- Bot Events ---

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord and is now online!')
    
    # CRUCIAL SYNCHRONIZATION LINE
    try:
        await bot.tree.sync() 
        print("Hybrid Commands Synced Successfully!")
    except Exception as e:
        print(f"Error during command sync: {e}")

# --- New Autocomplete Callback Function ---
async def hero_autocomplete(interaction: discord.Interaction, current: str):
    """Provides a list of heroes based on the user's current input."""
    
    # Get all hero names from your data and convert to lowercase for searching
    hero_names = [hero["name"] for hero in FRAG_HEROES]
    current_lower = current.lower()
    
    # Filter the list based on the user's input
    choices = [
        discord.app_commands.Choice(name=name, value=name)
        for name in hero_names 
        if current_lower in name.lower()
    ]
    
    # Discord limits choices to 25
    return choices[:25]

# --- New Role Autocomplete Callback ---
# Define the known roles in the FRAG game
FRAG_ROLES = ["Attacker", "Defender", "Wildcard", "Camp", "Center"] 

async def role_autocomplete(interaction: discord.Interaction, current: str):
    """Provides a list of FRAG roles based on the user's current input."""
    
    current_lower = current.lower()
    
    # Filter the list based on the user's input
    choices = [
        discord.app_commands.Choice(name=role, value=role)
        for role in FRAG_ROLES 
        if current_lower in role.lower() # Check if the input is anywhere in the role name
    ]
    
    return choices

# --- END OF NEW CODE BLOCK (STEP 1) ---


# --- Bot Commands ---

@bot.hybrid_command(name='hero_stats', description='Displays stats and ability for a hero', help='!hero_stats [HeroName] - Get a hero\'s full stats.')
@discord.app_commands.autocomplete(hero_name=hero_autocomplete)
async def hero_stats(ctx, *, hero_name):
    """Fetches and displays the details for a specific hero."""
    
    if isinstance(hero_name, (list, tuple)):
        input_name = " ".join(hero_name)
    else:
        input_name = str(hero_name)
    # 1. Normalize the input name for searching
    search_name = input_name.strip().lower()

    # 2. Search the data
    found_hero = next((h for h in FRAG_HEROES if h["name"].lower() == search_name), None)

    if found_hero:
        # 3. Create a clean embed message
        embed = discord.Embed(
            title=f"🔥 {found_hero['name']} - Hero Stats",
            description=f"*Role:* {found_hero['role']}\n*Rarity:* {found_hero['rarity']}",
            color=discord.Color.red()
        )
        embed.add_field(name="Weapon", value=found_hero['weapon'], inline=False)
        embed.add_field(name="Special Ability", value=found_hero['ability'], inline=False)
        embed.set_footer(text="Data provided by FRAG Bot Community")

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Hero *{hero_name}* not found. Check the spelling!")

# REPLACE THE OLD @bot.command(name='random_deck') WITH THIS:
@bot.hybrid_command(name='random_deck', description='Generates a balanced 5-hero deck (3 Attacker, 1 Defender, 1 Wildcard)', help='!random_deck - Get a random\ deck.')
async def random_deck(ctx):
    """Generates a role-balanced 5-hero deck."""
    
    # 1. Filter heroes by role
    attackers = [h for h in FRAG_HEROES if h['role'] == 'Attacker']
    defenders = [h for h in FRAG_HEROES if h['role'] == 'Defender']
    flex_heroes = [h for h in FRAG_HEROES if h['role'] in ['All-Rounder', 'Center', 'Wildcard', 'Camp']]
    
    # Check if we have enough heroes to form a balanced deck
    if len(attackers) < 3 or len(defenders) < 1 or len(flex_heroes) < 1:
        return await ctx.send("❌ Error: Not enough hero data to form a balanced deck (Need 2 Attackers, 1 Defenders, 1 Camps, 1 Wildcards). Please add more data!")
        
    # 2. Select the heroes based on the desired composition
    deck = []
    deck.extend(random.sample(attackers, 3))  # Select 3 Attackers
    deck.extend(random.sample(defenders, 1))  # Select 1 Defender
    deck.extend(random.sample(flex_heroes, 1)) # Select 1 Flex Hero
    
    # 3. Format the output (rest of the code is similar to before)
    main_hero = random.choice(deck)
    
    embed = discord.Embed(
        title="🎲 FRAG Balanced Deck Generator",
        description="A strategically balanced 5-hero squad (3/1/1 composition)!",
        color=discord.Color.from_rgb(255, 165, 0)
    )
    
    deck_list = ""
    for hero in deck:
        icon = "⭐" if hero["rarity"] == "Legendary" else "🔥"
        is_main = " (Suggested Main Hero)" if hero == main_hero else ""
        deck_list += f"{hero['role']}: {icon} *{hero['name']}*{is_main}\n"
        
    embed.add_field(name="Your Strategically Balanced Deck", value=deck_list, inline=False)
    embed.set_footer(text=f"Generated for {ctx.author.display_name}")

    await ctx.send(embed=embed)

    # --- New Bot Command: !counter_pick ---

@bot.hybrid_command(name='counter_pick', description='Suggests heroes good at countering the specified hero', help='!counter_pick [HeroName] - Get a counter pick of a hero.')
@discord.app_commands.autocomplete(hero_name=hero_autocomplete)
async def counter_pick(ctx, *, hero_name):
    """Suggests counters for a given hero based on predefined matchups."""
    
    if isinstance(hero_name, (list, tuple)):
        input_name = " ".join(hero_name)
    else:
        input_name = str(hero_name)
    
    # 1. Define Counter Logic (YOU MUST EXPAND THIS LIST!)
    # Key = Hero Being Countered (all lowercase)
    # Value = List of Recommended Counter Heroes (Title Case)

    # Normalize the input name for lookup
    search_name = input_name.strip().lower()

    # 2. Look up the counter heroes
    counters = COUNTER_MAP.get(search_name)

    if counters:
        counter_list = "\n".join([f"🔸 {hero}" for hero in counters])
        
        embed = discord.Embed(
            title=f"⚔️ Best Counter Picks for {hero_name.title()}",
            description="These heroes are generally strong against your opponent's pick:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Recommended Heroes", value=counter_list, inline=False)
        embed.set_footer(text="Use these heroes to gain an advantage!")
        
        await ctx.send(embed=embed)
    else:
        # If the hero isn't found in the counter map
        await ctx.send(f"❌ I don't have counter data for **{hero_name}** yet! Please check the spelling or contact the bot admin to update the data.")

# --- New Bot Command: !info ---

@bot.hybrid_command(name='info', description='Shows the full list of FRAG Bot commands', help='!info - Displays all available bot commands.')
async def info(ctx):
    """Provides general information and useful links."""
    
    embed = discord.Embed(
        title="🤖 FRAG Assistant Bot Information",
        description="Your dedicated tool for FRAG Pro Shooter strategy and data!",
        color=discord.Color.from_rgb(0, 150, 255) # Discord Blue
    )
    
    # 1. Main Commands
    embed.add_field(name="📜 Core Commands", 
                    value="""
                    !hero_stats [Name] - Get a hero's full stats and ability.
                    !random_deck - Get a balanced 5-hero deck (3 Attack, 1 Def, 1 Flex).
                    !counter_pick [Name] - Find strong counter heroes for any opponent.
                    """, 
                    inline=False)
                    
    # 2. Useful Links
    embed.add_field(name="🔗 Official FRAG Resources",
                    value="""
                    [Official FRAG Website](https://www.fragproshooter.com/)
                    [Latest Patch Notes](https://www.fragthegame.com)
                    [FRAG Wiki (Community Data)](https://fragproshooter.fandom.com/wiki/FRAG_Pro_Shooter_Wiki)
                    """,
                    inline=False)
                    
    # 3. Bot Status / Credit
    embed.set_footer(text=f"Bot created by {ctx.author.display_name} | Running on discord.py")

    await ctx.send(embed=embed)    

# --- New Bot Command: !tier_list ---

@bot.hybrid_command(name='tier_list', description='Displays top heroes for a given role (e.g., Attacker, Defender)', help='!tier_list [Role] - Get tier list of role.')
@discord.app_commands.autocomplete(role_name=role_autocomplete)
async def tier_list(ctx, *, role_name):
    """Displays heroes ranked by tier for a specific role."""

    if isinstance(role_name, (list, tuple)):
        input_name = " ".join(role_name)
    else:
        input_name = str(role_name)
    
    # 1. Normalize the input role for searching
    search_role = role_name.strip().title() # Capitalizes the first letter (e.g., 'attacker' -> 'Attacker')
    
    # Define a list of valid roles to check against
    VALID_ROLES = ['Attacker', 'Defender', 'Wildcard', 'Center', 'Camp']

    if search_role not in VALID_ROLES:
        valid_roles_str = ", ".join(VALID_ROLES)
        return await ctx.send(f"❌ Invalid Role. Please use one of the following: {valid_roles_str}")

    # 2. Filter and Sort Heroes
    # Filter by the requested role
    role_heroes = [h for h in FRAG_HEROES if h['role'] == search_role]
    
    # Define the tier order for sorting
    TIER_ORDER = {'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
    
    # Sort by tier rank
    sorted_heroes = sorted(role_heroes, key=lambda h: TIER_ORDER.get(h.get('tier', 'D'), 5)) # Defaults to 'D' tier if missing

    if not sorted_heroes:
        return await ctx.send(f"⚠ No heroes found for the role: *{search_role}*. Please check your hero_data.py.")

    # 3. Format the Output
    tier_lists = {'S': [], 'A': [], 'B': [], 'C': [], 'D': []}
    
    for hero in sorted_heroes:
        tier = hero.get('tier', 'D') # Default to 'D' if tier data is missing
        tier_lists[tier].append(f"{hero['name']} ({hero['rarity']})")

    embed = discord.Embed(
        title=f"🏆 Tier List for {search_role} Heroes",
        description=f"Community rankings for the best {search_role.lower()} heroes in the current meta.",
        color=discord.Color.gold()
    )

    # Add fields for each populated tier
    for tier, hero_names in tier_lists.items():
        if hero_names:
            hero_names_str = "\n".join(hero_names)
            embed.add_field(name=f"✨ Tier {tier}", value=hero_names_str, inline=True)

    await ctx.send(embed=embed)

# --- New Bot Command: !stats_compare ---

# Assuming you have the following autocomplete function defined elsewhere:
# async def hero_autocomplete(interaction: discord.Interaction, current: str): ...


@bot.hybrid_command(
    name='stats_compare', 
    aliases=['compare'], 
    description='Compares key stats of two heroes.',
    help='!stats_compare [Hero1] [Hero2] (Note: Use quotes for multi-word prefix commands)'
)
# Apply autocomplete to the first argument
@discord.app_commands.autocomplete(hero1=hero_autocomplete) 
# Apply autocomplete to the second argument
@discord.app_commands.autocomplete(hero2=hero_autocomplete)
async def stats_compare(ctx, hero1: str, hero2: str):
    """Compares the stats of two specified heroes."""
    
    # --- COMMAND LOGIC START ---
    
    # 1. Prepare names for lookup
    name1 = hero1.strip().lower()
    name2 = hero2.strip().lower()
    
    # 2. Lookup Hero 1 data
    # IMPORTANT: Ensure your FRAG_HEROES data structure and 'search_name' keys are correct.
    hero_data_1 = next((h for h in FRAG_HEROES if h.get('search_name') == name1), None)
    
    # 3. Lookup Hero 2 data
    hero_data_2 = next((h for h in FRAG_HEROES if h.get('search_name') == name2), None)
    
    # 4. Handle 'Hero Not Found' errors for both
    if not hero_data_1 or not hero_data_2:
        error_name = []
        if not hero_data_1:
            error_name.append(hero1)
        if not hero_data_2:
            error_name.append(hero2)
        
        await ctx.send(f"❌ Error: Could not find hero(es): {', '.join(error_name)}. Please check the spelling.")
        return

    # 5. YOUR ORIGINAL COMPARISON CODE GOES HERE:
    #    You now have the full data for hero_data_1 and hero_data_2 to work with.
    
    # --- Example of Comparison Output (Replace with your actual logic) ---
    
    # Create an embed for comparison
    embed = discord.Embed(
        title=f"📊 *{hero_data_1['name']}* vs *{hero_data_2['name']}*",
        color=discord.Color.blue()
    )
    
    # Example fields
    embed.add_field(name="Hero 1 Role", value=f"{hero_data_1.get('role', 'N/A')}", inline=True)
    embed.add_field(name="Hero 2 Role", value=f"{hero_data_2.get('role', 'N/A')}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer
    
    embed.add_field(name="Hero 1 Rarity", value=f"{hero_data_1.get('rarity', 'N/A')}", inline=True)
    embed.add_field(name="Hero 2 Rarity", value=f"{hero_data_2.get('rarity', 'N/A')}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

    embed.add_field(name="Hero 1 Role Tier", value=f"{hero_data_1.get('tier', 'N/A')}", inline=True)
    embed.add_field(name="Hero 2 Role Tier", value=f"{hero_data_2.get('tier', 'N/A')}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

    embed.add_field(name="Hero 1 Weapon", value=f"{hero_data_1.get('weapon', 'N/A')}", inline=True)
    embed.add_field(name="Hero 2 Weapon", value=f"{hero_data_2.get('weapon', 'N/A')}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

    embed.add_field(name="Hero 1 Special Ability", value=f"{hero_data_1.get('ability', 'N/A')}", inline=True)
    embed.add_field(name="Hero 2 Special Ability", value=f"{hero_data_2.get('ability', 'N/A')}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer


    await ctx.send(embed=embed)
    
    # --- COMMAND LOGIC END ---

# --- New Bot Command: !suggest_deck ---

@bot.hybrid_command(name='suggest_deck', description='Suggests a balanced deck built around a main hero', help='!suggest_deck [Hero] - Suggest a deck for your main hero.')
@discord.app_commands.autocomplete(hero_name=hero_autocomplete)
async def suggest_deck(ctx, *, hero_name):
    """Suggests a balanced 5-hero deck based on a main hero's preferred teammates."""
    
    if isinstance(hero_name, (list, tuple)):
        input_name = " ".join(hero_name)
    else:
        input_name = str(hero_name)
    
    # 1. Search for the main hero
    search_name = input_name.strip().lower()
    main_hero = next((h for h in FRAG_HEROES if h["name"].lower() == search_name), None)

    if not main_hero:
        return await ctx.send(f"❌ Hero *{hero_name}* not found in the database. Check the spelling!")
    
    # 2. Check for Teammate Data
    if not main_hero.get('teammates') or len(main_hero['teammates']) < 4:
        return await ctx.send(f"⚠ *{main_hero['name']}* is in the database, but suggested teammates are missing or incomplete! Please check the data.")

    # 3. Select 4 unique teammates randomly from the list
    # We select 4 teammates from the suggested list
    suggested_teammates = random.sample(main_hero['teammates'], 4)

    # 4. Filter and Get Full Data for Suggested Teammates
    # Create a list of the 4 suggested heroes' full data (not just names)
    teammate_heroes_data = []
    
    # Normalize the teammate list for easy lookup
    suggested_names_lower = [name.lower() for name in suggested_teammates]
    
    # Fetch the full hero data for the suggested teammates
    for hero in FRAG_HEROES:
        if hero['name'].lower() in suggested_names_lower:
            teammate_heroes_data.append(hero)
            
    # 5. Assemble the final deck and format output
    final_deck = [main_hero] + teammate_heroes_data
    
    embed = discord.Embed(
        title=f"💡 Deck Suggestion for {main_hero['name']} (Main)",
        description="A curated 5-hero squad designed to synergize with your main pick.",
        color=discord.Color.dark_green()
    )
    
    deck_list = ""
    for hero in final_deck:
        icon = "👑" if hero == main_hero else "🔸"
        tier = hero.get('tier', 'N/A')
        deck_list += f"{icon} *{hero['name']}* ({hero['role']} | Tier {tier})\n"
        
    embed.add_field(name="Your Synergistic Deck", value=deck_list, inline=False)
    embed.set_footer(text=f"Deck built around {main_hero['name']}'s strengths.")

    await ctx.send(embed=embed)


# --- Run the Bot ---

# ... (all your bot commands here) ...

if __name__ == "__main__":
    # Start web server FIRST
    keep_alive() 
    
    # Run bot SECOND
    try:
        bot.run(os.environ['DISCORD_TOKEN'])
    except Exception as e:
        print(f"Error starting bot: {e}")
