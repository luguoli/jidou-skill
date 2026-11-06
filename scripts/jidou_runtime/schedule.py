"""Timezone-aware recurrence calculation, independent of agents and shells."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import calendar
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import JidouError

UTC = timezone.utc
LEADS = {'不提醒': 0, '准时': 0, '提前10分钟': 10, '提前1小时': 60,
         '提前1天': 1440, '提前3天': 4320, '提前1周': 10080}
DAYS = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6}


def zone(name):
    try:
        return ZoneInfo(name)
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        raise JidouError('Unknown timezone or missing IANA data; install tzdata and use a valid timezone.') from None


def instant(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError
        return result
    except (ValueError, TypeError, AttributeError):
        raise JidouError('A timestamp with an explicit UTC offset is required.') from None


def stamp(value):
    return value.astimezone(UTC).isoformat(timespec='microseconds')


def localize(day, clock, tz):
    naive = datetime.combine(day, clock)
    valid = {}
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=tz, fold=fold)
        if candidate.astimezone(UTC).astimezone(tz).replace(tzinfo=None) == naive:
            valid[candidate.utcoffset()] = candidate
    if len(valid) != 1:
        raise JidouError('This local time is missing or ambiguous due to daylight saving; choose an explicit occurrence.')
    return next(iter(valid.values()))


def quiet(now, settings):
    hour = now.astimezone(zone(settings['timezone'])).hour
    start, end = settings['quiet_start_hour'], settings['quiet_end_hour']
    return hour >= start or hour < end if start > end else start <= hour < end


def chinese_number(value):
    if value.isdigit():
        return int(value)
    if value in {'正', '冬', '腊'}:
        return {'正': 1, '冬': 11, '腊': 12}[value]
    value = value.replace('初', '')
    digits = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if value.startswith('廿'):
        return 20 + (digits.get(value[1:], 0))
    if '十' in value:
        a, b = value.split('十')
        return (digits.get(a, 1) * 10) + digits.get(b, 0)
    if value in digits:
        return digits[value]
    raise JidouError('Unrecognized lunar date.')


@dataclass
class Rule:
    text: str | None
    tz: object
    lead: int = 0
    anchor: object = None
    override: object = None

    @classmethod
    def fields(cls, fields, timezone_name):
        raw = fields.get('重复', '')
        options = {}
        text = raw.strip()
        if text.startswith('{'):
            try:
                options = json.loads(text)
            except ValueError:
                raise JidouError('Invalid repeat-rule JSON.') from None
            if not isinstance(options, dict) or set(options) - {'rule', 'timezone', 'lead_minutes', 'anchor', 'override_reminder_at'}:
                raise JidouError('Unsupported repeat-rule keys.')
            text = options.get('rule')
            if text is not None and (not isinstance(text, str) or not text.strip()):
                raise JidouError('Repeat rule must be a nonempty string or null.')
        if not text:
            text = None
        lead = options.get('lead_minutes', LEADS.get(fields.get('提醒') or '不提醒'))
        if type(lead) is not int or lead < 0:
            raise JidouError('Lead minutes must be a nonnegative integer.')
        tz = zone(options.get('timezone', timezone_name))
        anchor = options.get('anchor') or fields.get('到期') or fields.get('记录时间')
        if anchor:
            anchor = localize(date.fromisoformat(anchor), time(9), tz) if re.fullmatch(r'\d{4}-\d{2}-\d{2}', anchor) else instant(anchor)
        override = instant(options['override_reminder_at']) if options.get('override_reminder_at') else None
        result = cls(text, tz, lead, anchor, override)
        if text:
            result.parts()
        return result

    def reminder_at(self, event, use_override=True):
        return self.override if use_override and self.override else event.astimezone(UTC) - timedelta(minutes=self.lead)

    def parts(self):
        text = self.text or ''
        anchor = re.search(r'[,，]\s*自\s*(\d{4}-\d{2}-\d{2})\s*起', text)
        if anchor:
            self.anchor = localize(date.fromisoformat(anchor.group(1)), time(9), self.tz)
            text = text[:anchor.start()]
        match = re.search(r'\s+(\d{1,2}):(\d{2})$', text)
        try:
            clock = time(int(match[1]), int(match[2])) if match else time(9)
        except ValueError:
            raise JidouError('Invalid recurrence clock time.') from None
        base = text[:match.start()] if match else text
        if base in {'每天', '每个工作日', '每工作日'}:
            return ('daily' if base == '每天' else 'weekday', None, clock)
        match = re.fullmatch(r'每(\d+)天', base)
        if match and int(match[1]) > 0:
            return 'interval', int(match[1]), clock
        match = re.fullmatch(r'每两周的周([一二三四五六日天])', base)
        if match:
            return 'biweekly', [DAYS[match[1]]], clock
        match = re.fullmatch(r'每周([一二三四五六日天](?:、(?:周)?[一二三四五六日天])*)', base)
        if match:
            return 'weekly', [DAYS[x] for x in match[1] if x in DAYS], clock
        if base == '每月最后一天':
            return 'monthlast', None, clock
        match = re.fullmatch(r'每月(\d{1,2})[号日]', base)
        if match and 1 <= int(match[1]) <= 31:
            return 'monthly', int(match[1]), clock
        match = re.fullmatch(r'每年(\d{1,2})月(\d{1,2})日', base)
        if match:
            try:
                date(2000, int(match[1]), int(match[2]))
            except ValueError:
                raise JidouError('Invalid annual date.') from None
            return 'annual', (int(match[1]), int(match[2])), clock
        match = re.fullmatch(r'每年农历(闰?)([正冬腊一二三四五六七八九十\d]+)月([初廿一二三四五六七八九十\d]+)', base)
        if match:
            month, day = chinese_number(match[2]), chinese_number(match[3])
            if not 1 <= month <= 12 or not 1 <= day <= 30:
                raise JidouError('Invalid lunar date.')
            return 'lunar', (month, day, bool(match[1])), clock
        raise JidouError('Unsupported recurrence; use the documented canonical rule forms.')

    def next(self, after):
        kind, value, clock = self.parts()
        local = after.astimezone(self.tz)
        if kind == 'lunar':
            try:
                from lunardate import LunarDate
            except ImportError:
                raise JidouError('Lunar recurrence requires lunardate; install requirements.txt.') from None
            for year in range(max(1900, local.year - 1), min(2100, local.year + 25)):
                try:
                    day = LunarDate(year, value[0], value[1], value[2]).toSolarDate()
                except ValueError:
                    continue
                candidate = localize(day, clock, self.tz)
                if candidate > after:
                    return candidate
            raise JidouError('No supported lunar occurrence was found; verify calendar range and leap month.')
        if kind == 'interval':
            if self.anchor is None:
                raise JidouError('Every-N-day recurrence needs a persistent anchor or first due date.')
            first = self.anchor.astimezone(self.tz).date()
            n = max(0, (local.date() - first).days // value)
            for step in (n, n + 1):
                candidate = localize(first + timedelta(days=step * value), clock, self.tz)
                if candidate > after:
                    return candidate
        if kind == 'biweekly' and self.anchor is None:
            raise JidouError('Biweekly recurrence needs a persistent anchor.')
        for offset in range(366 * 8):
            day = local.date() + timedelta(days=offset)
            if kind == 'weekday' and day.weekday() > 4:
                continue
            if kind in {'weekly', 'biweekly'} and day.weekday() not in value:
                continue
            if kind == 'biweekly':
                start = self.anchor.astimezone(self.tz).date()
                monday = start - timedelta(days=start.weekday())
                if day < start or ((day - monday).days // 7) % 2:
                    continue
            if kind == 'monthly' and day.day != value:
                continue
            if kind == 'monthlast' and day.day != calendar.monthrange(day.year, day.month)[1]:
                continue
            if kind == 'annual' and (day.month, day.day) != value:
                continue
            candidate = localize(day, clock, self.tz)
            if candidate > after:
                return candidate
        raise JidouError('No recurrence found in the supported planning horizon.')
