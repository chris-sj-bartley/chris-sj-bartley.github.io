---
layout: default
title: Projects
description: >-
  Software projects in endangered language technology, Manx Gaelic AI tools,
  speech synthesis, recognition, and voice conversion.
permalink: /projects/
---

<header class="page-header">
  <h1>Projects</h1>
</header>

## Gaelg AI

<a href="https://gaelgai.im">gaelgai.im</a> is a public web platform providing AI-powered tools for the Manx Gaelic language. Built as part of my doctoral research and maintained as an open resource for the Manx-speaking community.

The platform currently offers four tools, each trained on Manx language resources:

- **Text-to-speech** — Type or paste Manx text and hear it spoken aloud, with a choice of male and female voices and adjustable speed.
- **Automatic speech recognition** — Upload or record Manx audio to get an automatic transcription.
- **Translation** — Translate between Manx and English in either direction.
- **Audio timestamping** — Upload a Manx recording with its transcript to generate word- and phrase-level timestamps, useful for subtitling and corpus annotation.

The platform is hosted at the University of Sheffield and is free to use. Feedback and data contributions are welcome.

---

## Minimally Supervised Endangered Language ASR

*PhD project · Interspeech 2026 and [arXiv preprint](https://arxiv.org/abs/2510.04832)*

Nearly half of the world's ~7,000 languages are endangered, and one disappears roughly every two weeks. Automatic speech recognition (ASR) can make oral archives usable for learners, educators, and researchers, yet most endangered languages remain unsupported — not because they lack recorded speech, but because they lack it in the one format modern pipelines demand: an **utterance-level corpus** of segmented 3–15 second speech–text pairs. Building such a corpus is costly, and the prevailing alternative — fine-tuning billion-parameter multilingual models — assumes compute that most language communities cannot afford.

What these communities *do* have is different in kind. **Short-form** resources — isolated words and phrases from spoken dictionaries and pronunciation sites (Forvo, FirstVoices, Talking Dictionaries) — exist for hundreds of languages. **Long-form** recordings — interviews, broadcasts, folklore, audiobooks — exist in abundance but come as continuous audio with loosely matched transcripts. This project asks how little data, and in what form, is actually needed to build ASR, and whether these "in-the-wild" resources can stand in for a conventional corpus. The work is CPU-only throughout, built on HMM systems with the Kaldi toolkit, so that training and inference stay within reach of the communities it serves.

The line of work spans two papers that share this motivation but diverge in their experiments:

- **How I Built ASR for Endangered Languages with a Spoken Dictionary** (preprint) probes the **minimum requirements**. On Manx, 40 minutes of multi-speaker spoken-dictionary audio produces a usable baseline (<50% WER), and as little as 8 minutes is enough to bootstrap forced alignment of long-form recordings; adding domain-matched segments then reaches usable transcription (<25% WER). Source *diversity* — across speakers, styles, and domains — matters more than raw quantity. The work delivers the first ASR systems and the first utterance-level corpora for Manx (18 hours) and Cornish (39 hours).
- **Bootstrapping Endangered Language ASR with Short-Form Corpora** (Interspeech 2026) tests **generality and scale**. Using English (LibriSpeech), it first establishes that word-level supervision is a viable substitute for utterance-level data — word error rate stays stable until segments fall below about one second. It then applies the short-form-to-long-form pipeline across five typologically diverse languages (Cornish, Hawaiian, Jejueo, Manx, Mohawk), creating and open-sourcing a new utterance-level corpus for each, and benchmarks the results against state-of-the-art multilingual models.

Common threads across both:

- **A short-form → long-form alignment pipeline.** A monophone GMM–HMM trained on short-form audio bootstraps Viterbi forced alignment of long-form recordings, which a bootstrapped triphone model then decodes and segments — turning loosely transcribed audio into new utterance-level training data. A Unicode graphemic lexicon removes the need for a phonemic pronunciation dictionary, which most endangered languages lack.
- **New, open-sourced corpora** for Manx, Cornish, and (in the Interspeech work) Hawaiian, Jejueo, and Mohawk — languages that previously had no utterance-level speech resources.
- **Compute-efficient systems that hold their own against far larger models.** CPU-trained HMM systems, strengthened with web-text language models, beat zero-shot Omnilingual ASR, MMS, and Whisper on out-of-domain tests in nearly every language, at a fraction of the compute; where text is too scarce for a strong language model, a fine-tuned Whisper takes over. External language models were decisive for the HMM systems, worth on the order of 20 WER points on the hardest domains.

Taken together, the two papers show that the barrier to entry for endangered-language ASR — in both quantity and form of data — is far lower than commonly assumed, and that the resources communities already create can be turned into working transcription technology.

---

## Domain Adaptation

*PhD project, 2025– · ICASSP 2027, in preparation*

The corpus-building work above yields ASR that transcribes speech resembling its training data well, but degrades sharply **out of domain**. Systems built from read or single-speaker recordings handle matched material accurately, yet stumble on the spontaneous speech — filled pauses, reduced articulation, variable rate, unfamiliar speakers — that dominates real archives. The Cornish system, for example, reached under 8% word error rate on in-domain read speech but over 70% on a spontaneous interview; across the five-language study, the same read↔spontaneous and speaker mismatch inflated out-of-domain error everywhere. Because endangered-language data is scarce and skewed toward whatever domain happened to be recorded, this **mismatch — not a shortage of data as such — is often the binding constraint** on usable ASR.

This project asks whether **voice conversion (VC)** can close that gap as an offline **data-augmentation** step: take the abundant read speech a system is trained on, convert it toward the spontaneous, multi-speaker conditions it will meet at test time, and train on the result, manufacturing domain-matched data where none exists. The obstacle is that voice conversion is itself hard to supervise. A supervised approach needs pairs of utterances that share a word sequence but differ on the target attribute — speaker, accent, or speaking style — and the chance of a word sequence recurring across speakers falls exponentially with its length, so such pairs are widely assumed unobtainable. Most of the field therefore turns to unsupervised, disentanglement-based methods, which work well for timbre (isolating *who* is speaking) but struggle with accent and read/spontaneous style, which turn on *how* something is said.

The ICASSP 2027 paper, **Supervising Voice Conversion with Sub-Utterance Pairs**, challenges the assumption that parallel data is out of reach. A length-*n* sliding window over transcripts recovers *real* parallel supervision — transcript-matched sub-utterance segment pairs — from ordinary non-parallel corpora, with no collection and no synthesis: the source-to-target difference is simply given by the data, and can be learned end-to-end rather than imposed through hand-designed features. → [**Listen to sample training pairs**](/research/pair-corpora/)

Its contributions:

- A **sliding-window transcript-matching scheme** that recovers real parallel supervision from existing non-parallel corpora.
- Evidence that competitive **timbre, accent, and read/spontaneous style** conversion models can be trained on the resulting sub-utterance pairs.
- A finding that **diffusion probabilistic models** outperform alternative architectures under this paradigm.
- A measurement of the **minimum sub-utterance length** at which conversion stays viable — shorter segments are far more plentiful but carry less context, and the two trade off against each other.
- A demonstration of utility on the **ASR data-augmentation task** that motivates the work: read speech converted toward spontaneous domains and used to train acoustic models across a read→spontaneous test continuum.

Where the [Minimally Supervised Endangered Language ASR](#minimally-supervised-endangered-language-asr) line addresses the *data-format* problem — building ASR at all from unconventional resources — this line addresses the *domain-mismatch* problem that remains once a system exists. The two are complementary.

---

## Other work

**COM4511/6511 Speech Processing** — Teaching materials and marking support for the University of Sheffield's speech technology module, covering MFCC extraction, keyword spotting, VAD, GMMs, and K-means clustering.
