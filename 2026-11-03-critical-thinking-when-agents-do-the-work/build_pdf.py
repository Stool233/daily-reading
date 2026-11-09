#!/usr/bin/env python3
"""Build the complete Chinese Markdown and PDF from aligned translation blocks.

Requirements: Python 3.9+ and reportlab. Fonts are embedded as subsets.
The default font paths refer to macOS system fonts. Font files are not copied.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate,
    Paragraph, Spacer,
)

ROOT = Path(__file__).resolve().parent
HEADING_LINES = (7, 15, 23, 33, 41, 51, 57, 63)
INK = colors.HexColor('#202B30')
MUTED = colors.HexColor('#5B6C74')
ACCENT = colors.HexColor('#176E71')
RULE = colors.HexColor('#D9E3E3')
WIDTH, HEIGHT = A4
MARGIN = 55
NO_LINE_START = set('，。、：；？！）》」』】〕〉〗〙〛％‰…’”,.;:!?)]}%')
NO_LINE_END = set('（《「『【〔〈〖〘〚“‘([{')


def emphasized_prefix(line_number, text, html=False):
    """Highlight the original questions/reminders without changing wording."""
    delimiter = '？' if 17 <= line_number <= 22 else '。'
    eligible = 17 <= line_number <= 22 or 64 <= line_number <= 71
    if eligible and delimiter in text:
        prefix, rest = text.split(delimiter, 1)
        prefix += delimiter
        if html:
            return '<b>' + escape(prefix) + '</b>' + escape(rest)
        return '**' + prefix + '**' + rest
    return escape(text) if html else text


def typeset_body(line_number, text, width):
    """Fit mixed Latin/CJK text while keeping punctuation off invalid line edges.

    Explicit line breaks avoid ReportLab's mixed-fragment CJK edge cases.
    Latin words stay intact; the exact text is retained apart from line spaces.
    """
    delimiter = '？' if 17 <= line_number <= 22 else '。'
    emphasized = 17 <= line_number <= 22 or 64 <= line_number <= 71
    bold_end = text.find(delimiter) + 1 if emphasized and delimiter in text else 0
    tokens = []
    for match in re.finditer(r"[A-Za-z0-9]+(?:[._/'’\-][A-Za-z0-9]+)*|[ \t]+|.", text):
        value = match.group()
        bold = match.start() < bold_end
        font = 'BodyBold' if bold else 'Body'
        tokens.append((value, bold, pdfmetrics.stringWidth(value, font, 12)))

    lines = []
    start = 0
    while start < len(tokens):
        while start < len(tokens) and tokens[start][0].isspace():
            start += 1
        if start == len(tokens):
            break
        end, occupied = start, 0
        while end < len(tokens) and occupied + tokens[end][2] <= width - 0.5:
            occupied += tokens[end][2]
            end += 1
        if end == start:
            raise ValueError(f'Unbreakable token exceeds the line width: {tokens[start][0]}')
        if end < len(tokens):
            while end > start:
                left = end - 1
                while left >= start and tokens[left][0].isspace():
                    left -= 1
                right = end
                while right < len(tokens) and tokens[right][0].isspace():
                    right += 1
                valid_left = left >= start and tokens[left][0][-1] not in NO_LINE_END
                valid_right = right == len(tokens) or tokens[right][0][0] not in NO_LINE_START
                if valid_left and valid_right:
                    break
                end -= 1
            if end == start:
                raise ValueError(f'No legal CJK line break in paragraph {line_number}')
        row = tokens[start:end]
        while row and row[-1][0].isspace():
            row.pop()
        fragments = []
        for value, bold, _ in row:
            value = escape(value)
            fragments.append('<b>' + value + '</b>' if bold else value)
        lines.append(''.join(fragments))
        start = end
    return '<br/>'.join(lines)


def write_markdown(meta, segments):
    preface = (
        f"# {meta['title_zh']}\n\n"
        f"> 原文：[{meta['title']}]({meta['source']})\n>\n"
        f"> 作者：{meta['author']}（@addyosmani）\n>\n"
        "> 阅读与翻译日期：2026-11-09\n\n"
        "译者说明：以下完整翻译用户提供的文本，共 64 个正文段落与 8 个小标题，"
        "顺序与原文一致。正文中的第一人称均指作者。术语说明及阅读讨论另见"
        "[阅读笔记](notes.md)。原帖标题和日期的核对方式见[元信息](meta.json)。\n\n"
        "<!-- translation:start -->\n\n"
    )
    paragraphs = []
    for number, text in enumerate(segments, 1):
        if number in HEADING_LINES:
            paragraphs.append('## ' + text)
        else:
            paragraphs.append(emphasized_prefix(number, text))
    (ROOT / 'translation.zh.md').write_text(
        preface + '\n\n'.join(paragraphs) + '\n\n<!-- translation:end -->\n',
        encoding='utf-8',
    )


class ReadingDocument(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'section_key'):
            self.canv.bookmarkPage(flowable.section_key)
            self.canv.addOutlineEntry(
                flowable.section_title, flowable.section_key, level=0, closed=False,
            )


def decorate_page(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(ACCENT)
        canvas.rect(MARGIN, HEIGHT - 47, 29, 3, fill=1, stroke=0)
    else:
        canvas.setFont('Sans', 8.3)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, HEIGHT - 34, '当智能体替你工作时')
        canvas.drawRightString(WIDTH - MARGIN, HEIGHT - 34, 'Addy Osmani / 完整中文译本')
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, HEIGHT - 43, WIDTH - MARGIN, HEIGHT - 43)
        canvas.line(MARGIN, 42, WIDTH - MARGIN, 42)
        canvas.setFont('Sans', 8)
        canvas.drawString(MARGIN, 27, 'DAILY READING  /  2026.11.09')
        canvas.drawRightString(WIDTH - MARGIN, 27, str(doc.page).zfill(2))
    canvas.restoreState()


def build_pdf(meta, segments, args):
    fonts = (
        ('Body', args.body_font, args.body_index),
        ('BodyBold', args.body_font, args.body_bold_index),
        ('Sans', args.sans_font, args.sans_index),
    )
    for name, path, index in fonts:
        pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=index))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold')
    pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans')
    for name, _, _ in fonts:
        coverage = pdfmetrics.getFont(name).face.charWidths
        missing = sorted({c for text in segments for c in text
                          if not c.isspace() and ord(c) not in coverage})
        if missing:
            raise ValueError(f'{name} lacks glyphs: {missing}')

    base = dict(textColor=INK, alignment=TA_LEFT, wordWrap='CJK')
    body = ParagraphStyle(
        'BodyText', fontName='Body', fontSize=12, leading=21,
        spaceAfter=10, allowWidows=0, allowOrphans=0, **base,
    )
    heading = ParagraphStyle(
        'Section', fontName='Sans', fontSize=16, leading=24,
        spaceBefore=17, spaceAfter=11, keepWithNext=True, **base,
    )
    label = ParagraphStyle(
        'Label', fontName='Sans', fontSize=9, leading=14,
        textColor=ACCENT, wordWrap='CJK', spaceAfter=15,
    )
    cover_title = ParagraphStyle(
        'CoverTitle', fontName='Sans', fontSize=29, leading=42,
        spaceAfter=13, **base,
    )
    cover_english = ParagraphStyle(
        'CoverEnglish', fontName='Sans', fontSize=12, leading=18,
        spaceAfter=20, textColor=MUTED,
    )
    byline = ParagraphStyle(
        'Byline', fontName='Sans', fontSize=12, leading=20,
        spaceAfter=7, **base,
    )
    small = ParagraphStyle(
        'Small', fontName='Sans', fontSize=9.2, leading=16,
        textColor=MUTED, wordWrap='CJK', spaceAfter=8,
    )
    contents = ParagraphStyle(
        'Contents', fontName='Sans', fontSize=10.7, leading=19,
        spaceAfter=3, **base,
    )

    destination = ROOT / meta['files']['pdf']
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = ReadingDocument(
        str(destination), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=63, bottomMargin=58, title=meta['title_zh'],
        author=meta['author'], subject='用户提供全文的完整中文译本',
        creator='Daily Reading / ReportLab', pageCompression=1,
    )
    frame = Frame(
        MARGIN, 58, WIDTH - 2 * MARGIN, HEIGHT - 121,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    document.addPageTemplates(PageTemplate(id='Reading', frames=frame, onPage=decorate_page))

    story = [
        Spacer(1, 8),
        Paragraph('DAILY READING  /  完整中文译本', label),
        Paragraph('当智能体替你工作时，<br/>如何保持批判性思考', cover_title),
        Paragraph(escape(meta['title']), cover_english),
        Paragraph('Addy Osmani', byline),
        Paragraph('阅读与翻译  2026.11.09', small),
        Spacer(1, 6),
        HRFlowable(width='100%', thickness=0.7, color=RULE),
        Spacer(1, 18),
        Paragraph('本文目录', byline),
    ]
    for section, line_number in enumerate(HEADING_LINES, 1):
        title = escape(segments[line_number - 1])
        story.append(Paragraph(
            f'<link href="#section-{section}" color="#176E71">{section:02d}  {title}</link>',
            contents,
        ))
    story.extend([
        Spacer(1, 20),
        Paragraph(
            '译本说明：全文依据用户提供的英文文本翻译，保留全部段落与章节顺序。'
            '正文中的“我”均指作者；阅读讨论单独保存。', small,
        ),
        Paragraph(
            f'来源：<link href="{meta["source"]}" color="#176E71">'
            'X / @addyosmani / 原始帖子</link>', small,
        ),
        Paragraph(meta['source'], small),
        PageBreak(),
    ])
    section = 0
    for number, text in enumerate(segments, 1):
        if number in HEADING_LINES:
            section += 1
            item = Paragraph(escape(text), heading)
            item.section_key = f'section-{section}'
            item.section_title = text
        else:
            item = Paragraph(typeset_body(number, text, WIDTH - 2 * MARGIN), body)
        story.append(item)
    document.build(story)
    print(json.dumps({
        'pdf': str(destination), 'pages': document.page,
        'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'translated_blocks': len(segments), 'embedded_fonts': [x[0] for x in fonts],
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--body-font', type=Path,
                        default=Path('/System/Library/Fonts/Supplemental/Songti.ttc'))
    parser.add_argument('--body-index', type=int, default=6)
    parser.add_argument('--body-bold-index', type=int, default=1)
    parser.add_argument('--sans-font', type=Path,
                        default=Path('/System/Library/Fonts/STHeiti Medium.ttc'))
    parser.add_argument('--sans-index', type=int, default=1)
    args = parser.parse_args()
    meta = json.loads((ROOT / 'meta.json').read_text(encoding='utf-8'))
    source = (ROOT / 'source.txt').read_text(encoding='utf-8').splitlines()
    segments = json.loads((ROOT / 'translation.segments.json').read_text(encoding='utf-8'))
    if len(source) != len(segments) or len(segments) != 72:
        raise ValueError('Expected all 72 original and translated blocks.')
    if any(not isinstance(text, str) or not text.strip() for text in segments):
        raise ValueError('Every source block needs a nonempty translation.')
    write_markdown(meta, segments)
    build_pdf(meta, segments, args)


if __name__ == '__main__':
    main()
