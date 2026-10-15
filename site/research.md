---
layout: default
title: Research
description: >-
  Research on speech technology for endangered languages: building Manx speech
  corpora, ASR from short-form and long-form resources, and voice conversion
  for domain adaptation.
permalink: /research/
---

<header class="page-header">
  <h1>Research</h1>
  <p class="page-subtitle">
    The research problems behind my work, roughly in the order I took them on.
    For the story so far and the tools I've built, see the
    <a href="{{ '/' | relative_url }}">home page</a>.
  </p>
</header>

## Collecting and aligning Manx speech {#manx-speech-corpus}

*PhD project, 2024–*

When I began my PhD, Manx had no utterance-level speech corpus: the collection of short, transcribed clips that speech recognition is normally trained on. It did have recordings. I gathered more than 300 hours of them, from spoken dictionary entries and pronunciation sites to broadcasts, interviews and folklore archives.

Almost none of that audio was ready to use. Dictionary entries are single words; long recordings come with transcripts that only loosely line up with the audio. Using the alignment pipeline described [below](#endangered-language-asr), I turned this material into the first utterance-level corpus of Manx, with 18 hours of aligned speech in the first release.

---

## Endangered language ASR from short-form corpora {#endangered-language-asr}

*PhD project · [Interspeech 2026](https://www.isca-archive.org/interspeech_2026/bartley26_interspeech.html) and [arXiv preprint](https://arxiv.org/abs/2510.04832)*

Automatic speech recognition (ASR) can make oral archives usable for learners, teachers and researchers, yet most endangered languages remain unsupported. This is usually not because they lack recorded speech, but because they lack it in the one format modern pipelines demand: an utterance-level corpus of segmented 3–15 second speech–text pairs. Building one is costly, and the usual alternative, fine-tuning billion-parameter multilingual models, assumes compute that most language communities cannot afford.

What communities *do* have is different in kind. **Short-form** resources, isolated words and phrases from spoken dictionaries and pronunciation sites, exist for hundreds of languages. **Long-form** recordings, such as interviews, broadcasts, folklore and audiobooks, exist in abundance but come as continuous audio with loosely matched transcripts. This project asks how little data, and in what form, is really needed to build ASR, and whether these resources can stand in for a conventional corpus. Everything runs on CPU, using HMM systems built with Kaldi, so that training and use stay within reach of the communities the work is for.

The work spans two papers:

- **How I Built ASR for Endangered Languages with a Spoken Dictionary** ([preprint](https://arxiv.org/abs/2510.04832)) probes the **minimum requirements**. On Manx, 40 minutes of multi-speaker spoken-dictionary audio gives a usable baseline (under 50% WER), and as little as 8 minutes is enough to bootstrap alignment of long-form recordings; adding domain-matched segments then reaches usable transcription (under 25% WER). Diversity of speakers, styles and domains matters more than raw quantity. The paper delivers the first ASR systems and utterance-level corpora for Manx (18 hours) and Cornish (39 hours). [Watch the first Manx ASR demo](https://www.youtube.com/watch?v=0Gmi__3ZZFI), transcribing a local radio show.
- **Bootstrapping Endangered Language ASR with Short-Form Corpora** ([Interspeech 2026](https://www.isca-archive.org/interspeech_2026/bartley26_interspeech.html), [poster]({{ '/assets/posters/ukis2026-bootstrapping-endangered-language-asr.pdf' | relative_url }})) tests **generality and scale**. Using English, it shows that word-level supervision is a viable substitute for utterance-level data, with word error rate stable until segments fall below about one second. It then applies the pipeline to five typologically diverse languages (Cornish, Hawaiian, Jejueo, Manx and Mohawk), two of which (Jejueo and Mohawk) had never been supported by any ASR system, creating and open-sourcing a new utterance-level corpus for each, and benchmarks the results against state-of-the-art multilingual models.

Across both:

- **A short-form to long-form alignment pipeline.** A simple model trained on short-form audio bootstraps forced alignment of long-form recordings, which a stronger model then decodes and segments, turning loosely transcribed audio into new training data. A graphemic lexicon removes the need for a pronunciation dictionary, which most endangered languages lack.
- **New, open corpora** for languages that previously had no utterance-level speech resources.
- **Small systems that hold their own against far larger ones.** CPU-trained HMM systems with web-text language models beat zero-shot Omnilingual ASR, MMS and Whisper on out-of-domain tests in nearly every language. Where text is too scarce for a strong language model, a fine-tuned Whisper takes over.

---

## Voice conversion for domain adaptation {#voice-conversion-domain-adaptation}

*PhD project, 2025– · ICASSP 2027, in preparation*

The systems above transcribe speech that resembles their training data well, but degrade sharply **out of domain**. Models built from read or single-speaker recordings stumble on the spontaneous speech (filled pauses, reduced articulation, variable rate, unfamiliar voices) that dominates real archives. The Cornish system, for example, reached under 8% word error rate on read speech but over 70% on a spontaneous interview. Because endangered-language data is scarce and skewed towards whatever happened to be recorded, this mismatch, not a shortage of data as such, is often what decides whether a system is usable.

This project uses **voice conversion as data augmentation**: take the read speech a system is trained on, convert it towards the speakers, accents and speaking styles it will meet at test time, and train on the result. The obstacle is that voice conversion is itself hard to supervise. A supervised approach needs pairs of recordings that share their words but differ in the target attribute, and the chance of a sentence recurring across speakers falls off quickly with its length, so such pairs are widely assumed to be out of reach. Most of the field therefore uses unsupervised methods, which work well for changing *who* is speaking but struggle with accent and style, which are about *how* something is said.

The paper, **Supervising Voice Conversion with Sub-Utterance Pairs**, challenges that assumption. A sliding window over transcripts finds short runs of words or phones spoken by different speakers, recovering real paired training data from ordinary corpora with no extra recording and no synthesis.

Contributions:

- A **sliding-window transcript-matching scheme** that recovers real parallel supervision from existing non-parallel corpora.
- Evidence that competitive **speaker, accent and read/spontaneous style** conversion models can be trained on the resulting sub-utterance pairs.
- A finding that **diffusion models** outperform alternative architectures in this setting.
- A measurement of the **minimum sub-utterance length** at which conversion stays viable: shorter segments are far more plentiful but carry less context.
- A demonstration on the **ASR data-augmentation task** that motivates the work, with read speech converted towards spontaneous domains and used to train acoustic models.

Listen: [example training pairs]({{ '/research/pair-corpora/' | relative_url }}) · [converted speech samples]({{ '/samples/generated-samples/' | relative_url }})
