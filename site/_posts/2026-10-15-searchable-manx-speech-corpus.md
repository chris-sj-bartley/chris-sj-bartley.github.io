---
layout: post
title: "What is speech technology for? Searching 353 hours of spoken Manx"
date: 2026-10-15
description: "A searchable corpus of spoken Manx: type a word or phrase and jump to every point in 353 hours of community recordings where it is spoken."
crosspost: true   # propagate this post to the Gaelg AI blog
---

What is the point of speech and language technology? What is it actually useful for? The honest answer is a wide range of things, and which matters most depends on the most pressing problems a language community is facing.

There is also a gap between technology and its applications. To a lot of people, a speech recognition model is fairly abstract: hard to see, hard to use, easy to forget about. An application that solves a real problem is not. So alongside building speech recognition for Manx, I wanted to put it to work somewhere useful. The result is a [searchable corpus of spoken Manx](https://speech.gaelg.im/speech).

<!--more-->

## Decades of recordings you couldn't search

Over decades, the Manx community has created a wealth of naturally occurring speech: radio broadcasts, conversations recorded and shared on YouTube, readings of texts, and language-learning material. Text can be searched; audio, until now, could only be listened to from start to finish. If you wanted to hear how a particular word or phrase is used by real speakers, there was no practical way to find it.

## What it does

You type a word or phrase, and the search returns every place it is spoken, with a transcript showing it in its surrounding context. Each result has a timestamped link that takes you to the precise point in the original recording where it is said. In effect, it is an index of spoken Manx.

The corpus covers **11,903 recordings, 353 hours** in total.

<figure style="margin: 1.4rem 0; text-align: center;">
  <img src="{{ '/assets/images/blog/manx-speech-corpus/search-ayns-y-gharey.png' | absolute_url }}" alt="Search results for ayns y gharey, showing 154 matches in 64 recordings, each with a timestamp and the phrase highlighted in its transcript" style="max-width: 100%; height: auto; border-radius: 8px;" loading="lazy">
  <figcaption style="font-size: 0.85em; opacity: 0.7; margin-top: 0.4rem;">Searching for <em>ayns y gharey</em> ("in the garden") finds 154 matches across 64 recordings.</figcaption>
</figure>

## How it was built

- **Human transcripts** were included as they are.
- **Untranscribed recordings** were transcribed by several speech recognition systems fine-tuned for Manx. Where the systems agree, that agreement acts as a measure of confidence.
- **Everything was then force-aligned** with Kaldi, using the same alignment approach as [my research]({{ '/research/#endangered-language-asr' | absolute_url }}), so that every word has a timestamp.
- **Low-confidence segments and recordings**, where the systems disagree with each other, are flagged as such, so you know when to treat a transcript with care.

## Who it's for

Learners who want to hear a word or phrase used in real speech, by many different speakers. Educators looking for authentic examples. Researchers studying the language. And anyone with an interest in Manx. I shared it with Ynsee Gaelg, a Facebook group for Manx learners, and the feedback has been good.

## Thank you

The search is free and open to everyone. But none of it would exist without the people who created these recordings: the broadcasters, speakers, readers and teachers who, over decades, have put a huge amount of work into recording Manx and sharing it. This tool only makes their work easier to find. Every result links back to the original recording.

[Try the search](https://speech.gaelg.im/speech).
