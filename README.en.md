# Jidou · Quick Notes, Memos, To-do Lists & Reminders Skill

[简体中文](README.md) | **English**

**Your quick notes in chat. Capture ideas, save references, manage tasks, and set reminders.**

Jidou is an Agent Skill for **quick capture, AI note-taking, memos, to-do lists, and reminders**. Use your AI assistant as a personal notepad: jot down an idea, save a link or reading highlight, track tasks and deadlines, set birthday or recurring reminders, log a habit, and organize your notes into a personal knowledge base.

> “Make a quick note: could we generate weekly reports from chat history?”
>
> “Rent is due on the 5th of every month. Remind me two days before.”
>
> “What have I saved about Alex?”

## What you can use Jidou for

| What you need | How Jidou helps |
|---|---|
| Quick notes, memos, and sticky notes | Use chat as a notepad for quick capture, jotting things down, and everyday note-taking. |
| Idea capture and bookmarks | Collect ideas, save links, and keep reading highlights and book notes for later. |
| To-do lists and task management | Track tasks, deadlines, follow-ups, and daily plans. |
| Scheduled and advance reminders | Set event, birthday, anniversary, and lunar-calendar reminders. |
| Recurring reminders | Remember rent, bills, subscription renewals, and other daily, weekly, or monthly tasks. |
| Habit tracking and time management | Log daily check-ins for reading or exercise and review task progress. |
| Personal knowledge management | Search and organize saved notes into a personal knowledge base or second brain. |
| Weekly reviews and scheduled tasks | Summarize work notes for weekly reports and monthly reviews; schedule automatic organization when the required tools are connected. |

## Highlights

- **Quick capture in conversation.** No forms or special commands. Several separate items in one message become separate notes.
- **Notes, memos, and bookmarks together.** Save ideas, links, and reading highlights, with a clear summary and your original words available.
- **Keep developing an idea.** Add something today and something else next week, then review the thread together.
- **Follow tasks through to completion.** Move deadlines, mark tasks done, and check what is still on your to-do list.
- **Flexible recurring and birthday reminders.** Remember anniversaries, rent, bills, and lunar-calendar dates; reschedule, mute, or skip an occurrence.
- **Organize your knowledge and review progress.** Find old notes, review habit check-ins, and build a personal knowledge base. With the required tools connected, schedule weekly report preparation.

## Get started

Run this command in your terminal (requires Node.js/npm), then follow the prompts to choose your AI assistant:

```bash
npx skills add luguoli/jidou-skill
```

Alternatively, download the [skill package](https://github.com/luguoli/jidou-skill/archive/refs/heads/main.zip) and import it through your AI assistant’s skill interface. If your assistant supports installing skills, send it the repository URL:

> Install Jidou for me: https://github.com/luguoli/jidou-skill.git

Then try: **“Make a note: I want to organize my desk this week.”**

**Not tied to a platform or agent. Any assistant that supports the standard Skill format can load Jidou.** [Installation guide](references/install.en.md)

## Complete usage examples

Say these to your assistant, replacing the details with your own. You can speak English throughout.

### Quick notes, idea capture, and bookmarks

| What you want to do | Try saying |
|---|---|
| Save an idea | Make a note: could we generate weekly reports from chat history? |
| Save a reference | Save this link about cache penetration. Tag it backend and performance. |
| Keep a quotation | Save this passage exactly as written, and note that it’s from page 32 of the book. |
| Record a question | Note this question: why do the accounts never quite balance at the end of the month? |
| Keep a decision | We’ve decided to use template A because clients find it clearer. Save the reason too. |
| Record a plan | Make a plan: get the new content channel running within three months. |
| Add a task | Send the contract to Alex next Wednesday. |
| Keep a task without a date | Keep “file my taxes” on my list. I haven’t decided when yet. |
| Record an event | I have a health check on November 20 at 9 a.m. |
| Capture several things at once | Note two things: submit the proposal by Friday, and explore automating the weekly report. |
| Let Jidou categorize items | Note that I need to clean the air conditioner this weekend and pay the electricity bill at the end of the month. |
| Set a priority | This is due Thursday and other people depend on it. Make it a high priority. |

### Scheduled, recurring, and birthday reminders

| What you want to do | Try saying |
|---|---|
| A one-off reminder | Remind me about my health check on November 20 at 9 a.m. |
| A standard advance reminder | The meeting is Friday at 3 p.m. Remind me a day before. |
| A custom advance reminder | The meeting is Friday at 3 p.m. Remind me two hours before; the meeting time stays the same. |
| Every day | Remind me to read every evening at 9 p.m. |
| Weekdays | Remind me to choose today’s priorities every weekday at 9 a.m. |
| Several days each week | Remind me to exercise every Monday and Thursday at 8 p.m. |
| Every other week | Starting November 9, remind me to do a review every other Monday at 9 a.m. |
| Every few days | Starting November 8, remind me to check the plants every three days at 9 a.m. |
| A fixed day each month | Rent is due on the 5th of every month. Remind me two days before. |
| The end of each month | Remind me to reconcile the accounts at 6 p.m. on the last day of every month. |
| Every year | Remind me about our anniversary every March 28 at 9 a.m. |
| A lunar-calendar date | My mother’s birthday is the 28th day of the third Chinese lunar month. Remind me a day before it each year. |

“Weekdays” means Monday through Friday by default. Specify your region if you need public holidays and adjusted working days taken into account.

### Add details, reschedule, and complete tasks

| What you want to do | Try saying |
|---|---|
| Develop an earlier idea | Add this to the weekly report idea: start by collecting the tasks completed that week. |
| Correct a note | I got that wrong. It’s next Wednesday, not this Wednesday. |
| Move a one-off task | Move sending the contract to tomorrow at 3 p.m. |
| Change only this reminder | Remind me about rent on Saturday this time. Keep the usual schedule after that. |
| Change the ongoing schedule | From now on, move the exercise reminders to Wednesdays at 8 p.m. |
| Mute reminders temporarily | Don’t remind me about exercise for the rest of this week. |
| Complete one task | I’ve sent the contract to Alex. Mark that task done. |
| Complete one recurring occurrence | I’ve paid this month’s rent. Keep reminding me next month. |
| Skip an occurrence | Skip this week’s exercise reminder, then continue as usual next week. |
| Undo a mistake | That last check-in was a mistake. Undo that completion. |
| End a recurring series | I’ve canceled this subscription. Stop the renewal reminders. |
| Archive an old idea | I’m putting this idea aside. Archive it, but keep the note. |

### Note search, knowledge management, and reviews

| What you want to do | Try saying |
|---|---|
| Search by topic | What ideas about pricing did I save last month? |
| Search by person | What have I saved about Alex? |
| Review one area of life | What work tasks are still unfinished? |
| Review a time period | Show me what I saved this week. |
| Prioritize tasks | Which tasks should I tackle first? |
| Review an idea’s development | Show the weekly report idea from the first note through all the later additions. |
| Retrieve your original words | What exactly did I say when I first mentioned this proposal? |
| Rediscover old ideas | Pick a few old ideas for me to revisit. |
| Organize scattered notes | Organize this week’s notes by theme. |
| Reflect on progress | What did I actually finish this month, and what is still stuck? |
| Track a habit | Log today’s run and check how many days in a row I’ve kept it up recently. |

### Scheduled tasks and automatic organization

| What you want to do | Try saying |
|---|---|
| Run a script | Run the daily report script we’ve configured every morning at 7 a.m. |
| Check an API | Check this API every hour and tell me when something changes. |
| Organize notes on a schedule | Every Monday at 8 a.m., organize last week’s notes into a weekly report. |
| Run several steps | Every day at 6 p.m., fetch the data, generate the daily report, and send me the result. |
| Pause an action | Pause this daily report task until I ask you to resume it. |
| Resume an action | Resume the daily report task I paused. |

Reminders and scheduled actions need the relevant capabilities enabled; your assistant will tell you whether they are ready. Reminder timing can be affected by scan intervals and the execution environment. Scheduled actions need their tools configured first.

## Use your own words

You don’t need to memorize these phrases or use Chinese. Jidou follows your conversation language, and you can correct a category directly. Ordinary conversation is not saved automatically. If you specify a different place to save something, that choice is respected.

Version **2.14.1** · [MIT](LICENSE)
