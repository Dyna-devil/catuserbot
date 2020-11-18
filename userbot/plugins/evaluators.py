"""Execute GNU/Linux commands inside Telegram
Syntax: .exec Code"""
import asyncio
import io
import sys
import traceback

from ..utils import admin_cmd, edit_or_reply, sudo_cmd
from . import CMD_HELP, yaml_format


@bot.on(admin_cmd(pattern="bash (.*)"))
@bot.on(sudo_cmd(pattern="bash (.*)", allow_sudo=True))
async def _(event):
    if event.fwd_from or event.via_bot_id:
        return
    cmd = "".join(event.text.split(maxsplit=1)[1:])
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    OUTPUT = f"`{stdout.decode()}`"
    if len(OUTPUT) > Config.MAX_MESSAGE_SIZE_LIMIT:
        with io.BytesIO(str.encode(OUTPUT)) as out_file:
            out_file.name = "bash.text"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=cmd,
                reply_to=reply_to_id,
            )
            await event.delete()
    else:
        await edit_or_reply(event, OUTPUT)


@bot.on(admin_cmd(pattern="exec (.*)"))
@bot.on(sudo_cmd(pattern="exec (.*)", allow_sudo=True))
async def _(event):
    if event.fwd_from or event.via_bot_id:
        return
    cmd = "".join(event.text.split(maxsplit=1)[1:])
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    e = stderr.decode()
    if not e:
        e = "No Error"
    o = stdout.decode()
    if not o:
        o = "**Tip**: \n`If you want to see the results of your code, I suggest printing them to stdout.`"
    else:
        _o = o.split("\n")
        o = "`\n".join(_o)
    OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"
    if len(OUTPUT) > Config.MAX_MESSAGE_SIZE_LIMIT:
        with io.BytesIO(str.encode(OUTPUT)) as out_file:
            out_file.name = "exec.text"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=cmd,
                reply_to=reply_to_id,
            )
            await event.delete()
    else:
        await edit_or_reply(event, OUTPUT)


@bot.on(admin_cmd(pattern="eval (.*)"))
@bot.on(sudo_cmd(pattern="eval (.*)", allow_sudo=True))
async def _(event):
    if event.via_bot_id:
        return
    cmd = event.text.split(" ", maxsplit=1)[1]
    catevent = await edit_or_reply(event, "Processing ...")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = f"**•  Eval : **\n`{cmd}` \n\n**•  Result : **\n`{evaluation}` \n"
    await edit_or_reply(catevent ,text=final_output, aslink=True, linktext=f"**•  Eval : **\n`{cmd}` \n\n**•  Result : **\n")


async def aexec(code, smessatatus):
    message = event = smessatatus
    p = lambda _x: print(yaml_format(_x))
    reply = await event.get_reply_message()
    exec(f'async def __aexec(message, event , reply, client, p): ' +'\n event = smessatatus = message' + ''.join(f'\n {l}' for l in code.split('\n')))
    return await locals()['__aexec'](message, event ,reply, message.client, p)

CMD_HELP.update(
    {
        "evaluators": "**Plugin : **`evaluators`\
        \n\n  •  **Synatax : **`.eval <expr>`:\
        \n  •  **Function : **__Execute Python script.__\
        \n\n  •  **Synatax : **`.exec <command>`:\
        \n  •  **Function : **__Execute a bash command on catuserbot server and shows details.__\
        \n\n  •  **Synatax : **`.bash <command>`:\
        \n  •  **Function : **__Execute a bash command on catuserbot server and  easy to copy output__\
     "
    }
)
