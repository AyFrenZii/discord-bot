import discord
from discord import app_commands
from discord.ui import View, Button
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

GUILD_ID = 1112287034959212574
CHANNEL_COMPTA_ID = 1387816645442932736
CHANNEL_VOUCH_ID = 1287130199267475487
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def lire_soldes():
    with open("data.json", "r") as f:
        return json.load(f)

def ecrire_soldes(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def lire_paiements():
    with open("paiements.json", "r") as f:
        return json.load(f)

def ecrire_paiements(data):
    with open("paiements.json", "w") as f:
        json.dump(data, f, indent=4)

class VouchView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.add_item(Button(label=f"Rejoindre {channel.name}", url=f"https://discord.com/channels/{channel.guild.id}/{channel.id}"))

@tree.command(name="claiming", description="Prendre en charge une commande", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(montant="Le montant de la commande")
async def claiming(interaction: discord.Interaction, montant: int):
    soldes = lire_soldes()
    auteur = interaction.user.display_name

    if auteur not in soldes:
        soldes[auteur] = 0

    soldes[auteur] += montant
    ecrire_soldes(soldes)

    noms = list(soldes.keys())
    if len(noms) < 2:
        await interaction.response.send_message("❌ Il faut au moins deux personnes dans le fichier data.json.", ephemeral=True)
        return

    nom1, nom2 = noms[0], noms[1]
    solde1, solde2 = soldes[nom1], soldes[nom2]
    ecart = solde1 - solde2

    message = f"✅ **{auteur}** vient de claim **{montant}€** !\n\n"
    message += "__**📊 Solde actuel :**__\n"
    message += f"➜ **{nom1}** : `{solde1}€`\n"
    message += f"➜ **{nom2}** : `{solde2}€`\n\n"
    message += f"__**📈 Écart :**__ {abs(ecart)}€ {'🟢 en faveur de **' + nom1 + '**' if ecart > 0 else '🟢 en faveur de **' + nom2 + '**' if ecart < 0 else '⚖️ (équilibre parfait)'}"

    canal_compta = client.get_channel(CHANNEL_COMPTA_ID)
    if canal_compta:
        await canal_compta.send(message)
    else:
        print("Canal compta introuvable")

    await interaction.response.send_message(f"🎉 **Claim de {montant}€ enregistré avec succès !**", ephemeral=True)

    salon = interaction.channel
    await salon.edit(name=f"🔴-{auteur}")
    await salon.send(f"📌 La commande a bien été prise en charge par **{auteur}**.\nSi vous avez des questions, rejoignez notre [📱 Télégram](https://t.me/CyberLifeLounge) pour rester en contact au cas où on est Ban.")

@tree.command(name="timer", description="Démarrer un timer sur ce ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(duree="Durée en jours")
async def timer(interaction: discord.Interaction, duree: int):
    salon = interaction.channel
    await salon.edit(name=f"🟠-{interaction.user.display_name}")
    await interaction.response.send_message(f"⏳ Timer de {duree} jours démarré. On vous pingera à la fin.", ephemeral=True)

    async def attendre_et_notifier():
        await asyncio.sleep(duree * 86400)
        await salon.send(f"🔔 <@{interaction.user.id}> ton timer de {duree} jours est terminé ! Pense à vérifier ce ticket.")

    client.loop.create_task(attendre_et_notifier())

@tree.command(name="paiement_set", description="Configurer vos liens de paiement (facultatif)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(paypal="Lien PayPal (facultatif)", iban="Votre IBAN (facultatif)", crypto="Votre portefeuille crypto (facultatif)")
async def paiement_set(interaction: discord.Interaction, paypal: str = None, iban: str = None, crypto: str = None):
    data = lire_paiements()
    auteur = interaction.user.display_name

    if not paypal and not iban and not crypto:
        await interaction.response.send_message("❌ Veuillez fournir au moins un moyen de paiement.", ephemeral=True)
        return

    data[auteur] = {
        "PayPal": paypal if paypal else "Non renseigné",
        "IBAN": iban if iban else "Non renseigné",
        "Crypto": crypto if crypto else "Non renseigné"
    }
    ecrire_paiements(data)
    await interaction.response.send_message(
        "💳 Vos moyens de paiement ont été enregistrés avec succès !\n"
        f"🅿️ PayPal : {data[auteur]['PayPal']}\n"
        f"🏦 IBAN : {data[auteur]['IBAN']}\n"
        f"💸 Crypto : {data[auteur]['Crypto']}", ephemeral=True)

@tree.command(name="paiement", description="Afficher les moyens de paiement", guild=discord.Object(id=GUILD_ID))
async def paiement(interaction: discord.Interaction):
    data = lire_paiements()
    auteur = interaction.user.display_name

    if auteur not in data:
        await interaction.response.send_message("❌ Vous n'avez pas encore configuré vos moyens de paiements.", ephemeral=True)
        return

    infos = data[auteur]
    message = f"💰 **Moyens de Paiement de {auteur}** :\n\n"
    message += f"🅿️ PayPal : {infos['PayPal']}\n"
    message += f"🏦 IBAN : {infos['IBAN']}\n"
    message += f"💸 Crypto : {infos['Crypto']}"

    await interaction.response.send_message(message)

@tree.command(name="vouch", description="Obtenir le rôle client et accès au salon Vouch", guild=discord.Object(id=GUILD_ID))
async def vouch(interaction: discord.Interaction):
    guild = interaction.guild
    member = interaction.user
    canal_vouch = client.get_channel(CHANNEL_VOUCH_ID)
    role_client = guild.get_role(1145271388085690419)

    if role_client:
        await member.add_roles(role_client)
    else:
        await interaction.response.send_message("Rôle client introuvable.", ephemeral=True)
        return

    if canal_vouch:
        view = VouchView(canal_vouch)
        await interaction.response.send_message(
            "✅ Tu as été ajouté au rôle client ! Clique sur le bouton pour rejoindre le salon Vouch.",
            view=view,
            ephemeral=True
        )
    else:
        await interaction.response.send_message("Canal Vouch introuvable.", ephemeral=True)

@tree.command(name="claiming_reset", description="Réinitialiser les soldes de claiming", guild=discord.Object(id=GUILD_ID))
async def claiming_reset(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    ecrire_soldes({})
    await interaction.response.send_message("✅ Les soldes de claiming ont été remis à zéro.", ephemeral=True)

    canal_compta = client.get_channel(CHANNEL_COMPTA_ID)
    if canal_compta:
        await canal_compta.send("🔄 Tous les soldes de claiming ont été reset par un administrateur.")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{client.user} est connecté.")
    commandes = await tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
    print("Commandes dans le serveur :", [cmd.name for cmd in commandes])

client.run(TOKEN)
