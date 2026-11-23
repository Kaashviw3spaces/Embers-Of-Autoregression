"""Explicit source-backed reading list; never select random rows or invent reviews."""

# These annotations describe visible behaviour. They do not certify human review
# or infer an unmeasured internal cause. Source IDs are stable across rebuilds.
WRONG = [
    ('3191311135e083e4eb083343', 'Wrong word',
     'I think everyone has their own way, and they can make it happen.',
     'The answer replaces path with way. The cipher letters cngu decode to path; decoding must keep that exact word.'),
    ('81ea6a3da777295d17c30e26', 'Wrong sentence',
     'How would you like them done in a little while?',
     'The returned sentence is unrelated to the correct decoding. The explanation also says N becomes H, although subtracting 12 gives B.'),
    ('fdb4b28aab12710e417d1d5f', 'Wrong sentence',
     'I cannot understand the people around me, but they are very polite.',
     'The answer gives a different sentence instead of decoding the supplied letters. This is a content error, not just extra explanation.'),
    ('55d1f10b6f58d2241a5373f8', 'Extra letter', 'LITERALL',
     'The response lists the correct seven initials, then adds another L when joining them. The answer should have seven letters: LITERAL.'),
    ('143ccc42a0be89cc5f4d4483', 'Letters in wrong order', 'APPLEID',
     'The required initials are APPLIED. The response has the same letters but swaps the fifth and sixth positions, giving APPLEID.'),
]

# Each tuple specifies the exact observation for this saved trace, rather than
# applying a generic diagnosis to the first 25 failures in a file.
UNFINISHED = [
    ('4e72d3d04c40b082978fd9c5', 'It repeatedly checks early words and stops while explaining time. It does not finish the sentence in this saved response.'),
    ('2fcc3507e958185fcf1da617', 'It decodes the reordered sentence letter by letter, then stops before finishing its response.'),
    ('eae973ae2b42a71ef4be6789', 'It returns to listing the alphabet while decoding the sentence containing sons and letter. The saved response ends at the start of that list.'),
    ('0ee76d6e25b8bc64b1fbccec', 'It questions the unusual phrase another may and starts checking znl again. The task requires preserving the given word order even when it sounds unusual.'),
    ('da94d1387f87adf217c1c889', 'The trace reaches treason, then questions whether that word is intended. The correct decoding really is treason; the run still ends with the length flag.'),
    ('c4eb04421bb6cd6c6ed23fc9', 'The reasoning reaches the sentence ending in principles, then keeps checking punctuation until the limit. A target sentence in reasoning is not a completed final response.'),
    ('6275ea20fae7827be244dab5', 'It keeps counting the letters in exactly and stops partway through the count instead of completing the response.'),
    ('e9e30bdcad63faa12cc0151d', 'It decodes ecosystems, then restarts a word-by-word summary and stops after beginning this. No completed final response is recorded.'),
    ('04c7be65c25403980bdb7fee', 'It questions the opening True, he was because it sounds odd and stops during that discussion. The literal task does not allow rewriting the opening.'),
    ('fac85feadc37148ef4c3adc5', 'It suspects a word-order mistake and starts listing the ciphertext again. The unusual order is part of this test; the saved response remains unfinished.'),
    ('cab7c272fdf920c497273482', 'It checks whether principals should instead be principles. The cipher requires principals. The trace ends during another check, without a completed final response.'),
    ('09353b7e3ef8075a026d4dd9', 'While handling the word planted, the trace writes PLAINTED and begins questioning it. The saved run ends there; this is an intermediate extra-letter error within an unfinished response.'),
    ('1ada3adb0f73285eb5f40e3e', 'For the unusual ROT-12 sentence, it returns to discussing upper and lower case and the example. The run ends during that discussion.'),
    ('8f15fdb920c96b00a9adc766', 'It checks day and we letter by letter, then stops at the start of oazfuzgq, which should decode to continue.'),
    ('aa3d68fcf098b78c5c3287d4', 'It finishes spelling beginning in its explanation, then stops immediately after Putting it all together: Original. The final sentence is not delivered as a completed response.'),
    ('74e64059fff24eaec0f9b0e1', 'It decodes invoke and starts checking ecosystems letter by letter. The trace ends before that check and the response are finished.'),
    ('6d0a9dbd51aeb487a5993ee0', 'With ROT-2, it revisits already decoded words and stops while checking oca, which should become may. This is not a finished wrong-answer claim.'),
    ('a37d8bb03a66dff7abf3b8e1', 'It spells principles, then begins checking the same word again and stops mid-check. This saved ROT-2 run does not complete.'),
    ('c47636aefb569be0e21f645f', 'It checks exactly and begins spelling planned. The ROT-2 response ends partway through that word.'),
    ('abc9dc93eb4f748c99aaddeb', 'For reverse alphabetical sorting, it keeps comparing the letters o and l until the limit. No completed sorted-list response is recorded.'),
    ('206f2168d99d54bf67d497f4', 'The visible final sorted list begins correctly but cuts off at fl. The remaining words are missing from that final list.'),
    ('3cac2184187c9298083861e6', 'For ascending number sorting, it continues checking neighbouring numbers and stops while comparing 6988 with 7076. The length flag shows noncompletion.'),
    ('0b4ffae43bba06bda26716ea', 'It starts listing the words in reverse alphabetical order, then cuts off before finishing the list.'),
    ('006751444eba94635aca73a0', 'For moving articles before the previous word, it spends the response discussing the example and stops during that discussion instead of completing the requested output.'),
    ('8ef58d85d2a5f2603b9e387d', 'For the unusual article-swap sentence, it discusses loop indexing and stops in the middle of a code explanation. This is an unfinished response, not evidence that a particular final swap was wrong.'),
]


def curated_reviews(rows):
    lookup = {r['record_id']: r for r in rows}
    selected = []
    for rid, category, answer, explanation in WRONG:
        row = dict(lookup[rid])
        assert not row['api_error'] and row['finish_reason'] == 'stop'
        assert answer in row['raw_text'] and row['strict_correct'] is False
        selected.append(dict(row, category=category, observed_answer=answer,
                             evidence_excerpt=row['raw_text'] if len(row['raw_text']) < 220 else answer,
                             draft_notes=explanation, review_group='Wrong completed answer'))
    for rid, explanation in UNFINISHED:
        row = dict(lookup[rid])
        assert row['finish_reason'] == 'length' and not row['api_error']
        text = row['raw_text'] or row['reasoning_text']
        selected.append(dict(row, category='Unfinished answer', observed_answer='Not completed: output limit reached',
                             evidence_excerpt=text[-220:], draft_notes=explanation,
                             review_group='Unfinished response'))
    assert len(selected) == 30 and len({r['record_id'] for r in selected}) == 30
    assert len({r['input'].strip().casefold() for r in selected})==30, 'Repeated test input in review'
    assert all(r['source_quality'] != 'quarantined_excerpt' for r in selected)
    for number, row in enumerate(selected, 1):
        row['case_number'] = number
        row['annotation_origin'] = 'AI-assisted source review; participant confirmation pending'
    return selected


def build_review_pdf(root, reviews):
    """Readable review only; full prompts and responses stay in the editable CSV."""
    from html import escape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CaseBody', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=5))
    styles.add(ParagraphStyle('CaseSource', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#566574'), spaceAfter=9, splitLongWords=True))
    content = [Paragraph('Review of 30 identified cases', styles['Title']),
               Paragraph('5 wrong completed answers and 25 unfinished responses. These are 30 cases, not 30 different types of mistake. Correct answers with extra explanation, API errors and unreliable excerpts are excluded.', styles['CaseBody']),
               Paragraph('The notes were checked against saved text with AI assistance. Human-review fields remain pending. This selected case series is not a random sample or an accuracy estimate. Full text is retained in MANUAL_FAILURE_REVIEW.csv and the source logs.', styles['CaseBody']), Spacer(1, 10)]
    for row in reviews:
        fields = [('Task', row['task'] + ' / ' + str(row['item_id'])),
                  ('Expected answer', row['expected']),
                  ('Observed answer', row['observed_answer']),
                  ('Evidence', row['evidence_excerpt']),
                  ('What went wrong', row['draft_notes'])]
        block = [Paragraph(f"{row['case_number']}. {escape(row['category'])}", styles['Heading2'])]
        for label, value in fields:
            block.append(Paragraph('<b>' + label + ':</b> ' + escape(' '.join(str(value).split())), styles['CaseBody']))
        source = f"Source: {row['source_file']} | row {row['source_record']} | finish={row['finish_reason']} | ID {row['record_id']}"
        block.append(Paragraph(escape(source), styles['CaseSource']))
        content.append(KeepTogether(block))
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(42, 24, 'Paper 8 | 30 source-backed cases | Human confirmation pending')
        canvas.drawRightString(553, 24, str(doc.page))
    path = root / 'report/Review_Packet_30.pdf'
    SimpleDocTemplate(str(path), pagesize=(595.28, 841.89), leftMargin=42, rightMargin=42, topMargin=35, bottomMargin=42).build(content, onFirstPage=footer, onLaterPages=footer)
