import random
import sqlite3
import discord
from discord.ext import commands
from config import settings
from discord.ext.commands import cooldown, BucketType
from random import randint

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix= settings['PREFIX'], intents=discord.Intents.all())
conn = sqlite3.connect("server.db")
cursor = conn.cursor()

# подключение к таблице
@bot.event
async def on_ready():
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        name TEXT,
        id INT,
        cash BIGINT,
        server_id INT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS shop (
        role_id INT,
        id INT,
        cost BIGINT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS work (
            name_id INT,
            id INT,
            salary_min BIGINT,
            salary_max BIGINT
        )""")

    for guild in bot.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, {guild.id})")
            else:
                pass
    conn.commit()
    print('Bot connected')
#Добавление нового или уже сущ. пользователя в таблицу
@bot.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
        cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, {member.guild.id})")
        conn.commit()
    else:
        pass

#создание команды на просмотр баланса пользователя
@bot.command(aliases = ['$', 'balance'])
async def __balance(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(embed=discord.Embed(
            description=f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :pound:**"""
        ))

    else:
        await ctx.send(embed=discord.Embed(
            description=f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :pound:**"""
        ))

#команда для Администраторов - выдача валюты пользователю
@bot.command(aliases = ['award'])
@commands.has_any_role("Administrator", "OWNER", "Curator")
async def __award(ctx, member: discord.Member = None, amount: int = None):
    if member is None:
        await ctx.send(embed=discord.Embed(
            description=f"**{ctx.author}**, укажите пользователя, которому хотите выдать волюту!"
        ))
    else:
        if amount is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите сумму!"
            ))
        elif amount < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нахуя такая маленькая сумма?"
            ))
        else:
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
            conn.commit()
            await ctx.message.add_reaction('✅')

#Команда для Администраторов - отнять валюту у пользователя
@bot.command(aliases = ['take'])
@commands.has_any_role("Administrator", "OWNER", "Curator")
async def __take(ctx, member: discord.Member = None, amount = None):
    if member is None:
        await ctx.send(embed=discord.Embed(
            description=f"**{ctx.author}**, укажите пользователя, которому хотите отнять волюту!"
        ))
    else:
        if amount is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите сумму!"
            ))
        elif amount == 'all':
            cursor.execute("UPDATE users SET cash = cash = {} WHERE id = {}".format(0, member.id))
            conn.commit()
            await ctx.message.add_reaction('✅')
        elif int(amount) < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нахуя такая маленькая сумма?"
            ))
        else:
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, member.id))
            conn.commit()
            await ctx.message.add_reaction('✅')

#Команда на добавление ролей в магазин            
@bot.command(aliases = ['addshop'])
@commands.has_any_role("Administrator", "OWNER", "Curator")
async def __addshop(ctx, role: discord.Role = None, cost: int = None):
    if role is None:
        await ctx.send(embed = discord.Embed(
            description=f"**{ctx.author}**, укажите роль, которую хотите внести в мАгаААААзинчиг)"
        ))
    else:
        if cost is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите стоимость товара"
            ))
        elif cost < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нихуя ты щедрый, а ну ка повысь цену"
            ))
        else:
            cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
            conn.commit()
            await ctx.message.add_reaction('✅')

#Команда на удаление роли из магазина            
@bot.command(aliases = ['rshop'])
@commands.has_any_role("Administrator", "OWNER", "Curator")
async def __removeshop(ctx, role: discord.Role = None):
    if role is None:
        await ctx.send(embed = discord.Embed(
            description=f"**{ctx.author}**, укажите роль, которую хотите удалить к чертовой матери :3)"
        ))
    else:
        cursor.execute("DELETE FROM shop WHERE role_id = {}".format(role.id))
        conn.commit()
        await ctx.message.add_reaction('✅')

# Команда для просмотра списка ролей из магазина        
@bot.command(aliases = ['shop'])
async def __shop(ctx):
    embed = discord.Embed(title='Хайповый магазик ролей')
    for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {}".format(ctx.guild.id)):
        if ctx.guild.get_role(row[0]) != None:
            embed.add_field(
                name=f"Стоимость {row[1]}",
                value=f"Вы преобретете роль {ctx.guild.get_role(row[0]).mention}",
                inline=False
            )
        else:
            pass
    await ctx.send(embed=embed)

# Команда для покупки роли    
@bot.command(aliases = ['buy'])
async def __buy(ctx, role: discord.Role = None):
    if role is None:
        await ctx.send(embed = discord.Embed(
            description=f"**{ctx.author}**, укажите роль, которую хотите приобрести)"
        ))
    else:
        if role in ctx.author.roles:
            await ctx.send(embed=discord.Embed(
                description=f"Такая роль у вас присутствует"
            ))
        elif cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0] > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, дорогой ты мой, у тя деняг нет)"
            ))
        else:
            await ctx.author.add_roles(role)
            cursor.execute("UPDATE users SET cash = cash - {0} WHERE id = {1}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0], ctx.author.id))
            conn.commit()
            await ctx.message.add_reaction('✅')

#Команда для просмотра статистики            
@bot.command(aliases = ['top'])
async def __top(ctx):
    embed = discord.Embed(title='Топ 10 богачей сервера')
    counter = 0

    for row in cursor.execute("SELECT name, cash FROM users WHERE server_id = {} ORDER BY cash DESC LIMIT 10".format(ctx.guild.id)):
        counter+=1
        embed.add_field(
            name=f'# {counter} | `{row[0]}`',
            value=f'Баланс - {row[1]} :pound:',
            inline=False
        )
    await ctx.send(embed = embed)


# Команда на добавление работы в список работ    
@bot.command(aliases = ['addwork'])
async def __addwork(ctx, name: discord.Role = None, salary_min: int = None, salary_max: int = None):
    if name is None:
        await ctx.send(embed = discord.Embed(
            description=f"**{ctx.author}**, укажите работу, которыу хотите занести в список)"
        ))
    else:
        if salary_min is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите диапазон цены работы"
            ))
        elif salary_max is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите диапазон цены работы"
            ))
        elif salary_min < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нихуя ты щедрый, а ну ка повысь цену"
            ))
        elif salary_max < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нихуя ты щедрый, а ну ка повысь цену"
            ))
        else:
            cursor.execute("INSERT INTO work VALUES ({}, {}, {}, {})".format(name.id, ctx.guild.id, salary_min, salary_max))
            conn.commit()
            await ctx.message.add_reaction('✅')

# Команда на просмотр списка работ            
@bot.command(aliases = ['worklist'])
async def __worklist(ctx):
    embed = discord.Embed(title='Список работ сервера')
    for row in cursor.execute("SELECT name_id, salary_min, salary_max FROM work WHERE id = {}".format(ctx.guild.id)):
        if ctx.guild.get_role(row[0]) != None:
            embed.add_field(
                name=f"Зарплата - {row[1]} - {row[2]}",
                value=f"Профессия {ctx.guild.get_role(row[0]).mention}",
                inline=False
            )
        else:
            pass
    await ctx.send(embed=embed)


#Команда для получение валюты посредством работы (ограниченная команда)    
@bot.command(aliases = ['work'])
@commands.cooldown(1, 3600, commands.BucketType.user)
async def __work(ctx, name: discord.Role = None):
    if name is None:
        await ctx.send(embed = discord.Embed(
            description=f'Укажите роль(работу), за которую получите вознаграждение'
        ))
    else:
        s = random.randint(cursor.execute("SELECT salary_min FROM work WHERE name_id = {}".format(name.id)).fetchone()[0], cursor.execute("SELECT salary_max FROM work WHERE name_id = {}".format(name.id)).fetchone()[0])
        cursor.execute("UPDATE users SET cash = cash + {0} WHERE id = {1}".format(s, ctx.author.id))
        conn.commit()
        await ctx.message.add_reaction('✅')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed = discord.Embed(
            description=f'Для следующей смены осталось **{round(error.retry_after, 2)}** сек'
        ))

# Команда на перевод валюты другому пользователю        
@bot.command(aliases = ['transfer', 'tr'])
async def __transfer(ctx, member:discord.Member = None, amount:int = None):
    if member is None:
        await ctx.send(embed=discord.Embed(
            description=f"**{ctx.author}**, укажите пользователя, которому хотите передать волюту!"
        ))
    else:
        if amount is None:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, укажите сумму!"
            ))
        elif amount < 1:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, нахуя такая маленькая сумма?"
            ))
        elif amount > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
            await ctx.send(embed=discord.Embed(
                description=f"**{ctx.author}**, Указанная сумма больше вашего сбережения!"
            ))
        else:
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, ctx.author.id))
            conn.commit()
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
            conn.commit()
            await ctx.message.add_reaction('✅')

bot.run(settings['TOKEN'])
