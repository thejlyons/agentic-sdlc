# Design and taste work

Engineering cards end at "merged with review and green CI". Work judged by taste (art style, a screen's
look, a brand) does not have that kind of end, and the loop treats it differently.

How much this has been used: on one game prototype, for art-style pitches and the polish passes that
followed. A first round of four quick mockups was judged machine-made by the owner. A second round of ten
styles, made the way this page describes, landed well by his judgement. That is the whole evidence. Nothing
here has been measured.

## Parallel illustrator agents

One agent per style family, run in parallel, each with the same brief. Parallel agents with separate
context do not converge on one look the way a single agent producing ten options does. More styles than the
owner's first favourites are pitched on purpose, so he does not commit too early.

## The brief: craft rules, not adjectives

Every illustrator gets:

- **The exact same scene** for every option, so the styles are compared and not the subjects.
- **The real frame**: a portrait phone frame when the product is a phone game.
- **A list of banned generic tells**: bare circles standing in for objects, rainbow or neon gradients, emoji
  faces, uniform vector strokes, drop shadows on everything, centred-by-default layout.
- **Subject-correct anatomy.** The thing drawn has to be built like the thing.
- **A palette of four to six colours and one light source** per style.
- **Fonts chosen for the style's period**, never the two or three defaults every generated page uses.

## The render-critique-fix loop

Required, at least two rounds per option:

1. Render the work with a headless browser to a PNG.
2. Open the PNG and look at it. Judging the source is not looking.
3. Write a critique against the craft rules.
4. Fix, and render again.

It is the same discipline as the engineering loop's "open the pictures and read them", applied to drawings.

## One gallery, honest pros and cons

All options go on one gallery page, side by side, each with plain pros and cons: production cost,
readability at phone size, fit with the product's tone. The owner picks from pictures. Descriptions of
pictures are not accepted for visual choices anywhere in this system
([loop.md](loop.md), "What the owner is asked").

## An iteration, not done, until the owner accepts

The owner's rule (2026-11-15), after the lead treated a shipped design as finished and built on it:

- A change is reported as "a new iteration of X is live", never as done or final.
- Each element (for a game: map, paths, each screen, sound, writing) has a status with only two end states:
  **iterating**, or **accepted by the owner on a date**.
- An unaccepted element is not copied to new places, and dependent work is not stacked on it.
- The lead keeps proposing the next polish step for unaccepted elements.
- Workers are briefed the same way.

Only the owner declares an element final. This is separate from engineering cards, where Done keeps its
meaning.

## Where it fits in the loop

App UI cards still go through the normal loop: screenshots in light, dark and the largest text size, read by
the worker and again by the reviewer. A taste choice inside such a card comes to the owner as two or three
built options, screenshotted; small reversible ones may be decided by the lead after about 15 minutes
([dashboard.md](dashboard.md)).

Rules: [visual-pitches-need-a-craft-brief](../rules/visual-pitches-need-a-craft-brief.md),
[iterations-until-owner-accepts](../rules/iterations-until-owner-accepts.md).

## Open questions

Whether the loop holds up for production art, and not only pitches, is unproven. The critique is written by
the same model that drew the picture; there is no independent art reviewer yet. The illustrator brief is not
in this repo as a file, because the live one is specific to the prototype.
