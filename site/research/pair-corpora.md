---
layout: default
title: Cross-speaker pair corpora
description: >-
  Audio samples of cross-speaker, content-matched word and phone pairs mined
  from force-aligned LibriTTS, training supervision for diffusion voice
  conversion (DiffVC / Grad-VC).
permalink: /research/pair-corpora/
---

<header class="page-header">
  <h1>Cross-speaker pair corpora</h1>
</header>

<style>
  .samples { margin: 1.4rem 0; }
  .sample-box {
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-radius: 10px;
    padding: 0.2rem 1rem 1rem;
    margin: 1.2rem 0;
  }
  .sample-box > h3 { margin: 0.9rem 0 0.3rem; }
  .sample-box > p.box-sub { margin: 0 0 0.4rem; opacity: 0.7; font-size: 0.9em; }
  .table-wrap { overflow-x: auto; }
  table.sample-table { border-collapse: collapse; width: 100%; }
  .sample-table th, .sample-table td {
    padding: 0.5rem 0.6rem;
    text-align: left;
    vertical-align: middle;
    border-top: 1px solid rgba(128, 128, 128, 0.2);
  }
  .sample-table thead th {
    border-top: none;
    border-bottom: 2px solid rgba(128, 128, 128, 0.35);
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    opacity: 0.75;
  }
  .sample-table td.len {
    font-size: 1.35em;
    font-weight: 600;
    text-align: center;
    width: 2.5rem;
    border-top: 2px solid rgba(128, 128, 128, 0.4);
  }
  .sample-table td.tr { min-width: 9rem; }
  .sample-table .ph {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.85em;
    letter-spacing: 0.02em;
  }
  .sample-table .wp { opacity: 0.7; display: block; margin-top: 0.15rem; }
  .sample-table audio { height: 34px; width: 230px; max-width: 100%; display: block; }
  .sample-table .cap { font-size: 0.78em; opacity: 0.6; margin-top: 0.2rem; }
</style>

Each **pair** is the *same content spoken by two different speakers*, cut from
LibriTTS clean (`train-clean-100` + `train-clean-360`) using Montreal Forced
Aligner alignments. The **words** table matches on whole words; the **phones**
table matches on ARPABET phone sequences, which can begin or end mid-word; a
leading or trailing hyphen marks the cut. The left column is the length of the
matched unit.

<div class="samples" markdown="0">

<div class="sample-box">
<h3>Words</h3>
<div class="table-wrap">
<table class="sample-table">
<thead>
<tr><th>Words</th><th>Transcription</th><th>Speaker A</th><th>Speaker B</th></tr>
</thead>
<tbody>
<tr>
  <td class="len" rowspan="2">1</td>
  <td class="tr">"Beautiful"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n1/pair1/A_spk103.mp3' | relative_url }}"></audio><span class="cap">spk 103 · 0.51 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n1/pair1/B_spk1841.mp3' | relative_url }}"></audio><span class="cap">spk 1841 · 0.51 s</span></td>
</tr>
<tr>
  <td class="tr">"Together"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n1/pair2/A_spk1743.mp3' | relative_url }}"></audio><span class="cap">spk 1743 · 0.49 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n1/pair2/B_spk201.mp3' | relative_url }}"></audio><span class="cap">spk 201 · 0.49 s</span></td>
</tr>
<tr>
  <td class="len" rowspan="2">3</td>
  <td class="tr">"One of the"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n3/pair1/A_spk101.mp3' | relative_url }}"></audio><span class="cap">spk 101 · 1.14 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n3/pair1/B_spk2256.mp3' | relative_url }}"></audio><span class="cap">spk 2256 · 0.81 s</span></td>
</tr>
<tr>
  <td class="tr">"As soon as"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n3/pair2/A_spk231.mp3' | relative_url }}"></audio><span class="cap">spk 231 · 1.16 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n3/pair2/B_spk225.mp3' | relative_url }}"></audio><span class="cap">spk 225 · 0.99 s</span></td>
</tr>
<tr>
  <td class="len" rowspan="2">5</td>
  <td class="tr">"As a matter of fact"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n5/pair1/A_spk8772.mp3' | relative_url }}"></audio><span class="cap">spk 8772 · 1.29 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n5/pair1/B_spk7286.mp3' | relative_url }}"></audio><span class="cap">spk 7286 · 1.24 s</span></td>
</tr>
<tr>
  <td class="tr">"It seems to me that"</td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n5/pair2/A_spk8050.mp3' | relative_url }}"></audio><span class="cap">spk 8050 · 1.53 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/word_n5/pair2/B_spk6836.mp3' | relative_url }}"></audio><span class="cap">spk 6836 · 1.48 s</span></td>
</tr>
</tbody>
</table>
</div>
</div>

<div class="sample-box">
<h3>Phones</h3>
<div class="table-wrap">
<table class="sample-table">
<thead>
<tr><th>Phones</th><th>Transcription</th><th>Speaker A</th><th>Speaker B</th></tr>
</thead>
<tbody>
<tr>
  <td class="len" rowspan="2">1</td>
  <td class="tr"><span class="ph">IY</span><span class="wp">"the"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n1/pair1/A_spk103.mp3' | relative_url }}"></audio><span class="cap">spk 103 · 0.08 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n1/pair1/B_spk1034.mp3' | relative_url }}"></audio><span class="cap">spk 1034 · 0.08 s</span></td>
</tr>
<tr>
  <td class="tr"><span class="ph">AY</span><span class="wp">"by"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n1/pair2/A_spk1246.mp3' | relative_url }}"></audio><span class="cap">spk 1246 · 0.13 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n1/pair2/B_spk1263.mp3' | relative_url }}"></audio><span class="cap">spk 1263 · 0.13 s</span></td>
</tr>
<tr>
  <td class="len" rowspan="2">3</td>
  <td class="tr"><span class="ph">T DH AH</span><span class="wp">"-t the"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n3/pair1/A_spk1088.mp3' | relative_url }}"></audio><span class="cap">spk 1088 · 0.15 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n3/pair1/B_spk1116.mp3' | relative_url }}"></audio><span class="cap">spk 1116 · 0.15 s</span></td>
</tr>
<tr>
  <td class="tr"><span class="ph">N DH AH</span><span class="wp">"-n the"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n3/pair2/A_spk1098.mp3' | relative_url }}"></audio><span class="cap">spk 1098 · 0.15 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n3/pair2/B_spk1246.mp3' | relative_url }}"></audio><span class="cap">spk 1246 · 0.15 s</span></td>
</tr>
<tr>
  <td class="len" rowspan="2">7</td>
  <td class="tr"><span class="ph">W AH N AH V DH AH</span><span class="wp">"one of the"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n7/pair1/A_spk198.mp3' | relative_url }}"></audio><span class="cap">spk 198 · 0.36 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n7/pair1/B_spk2289.mp3' | relative_url }}"></audio><span class="cap">spk 2289 · 0.36 s</span></td>
</tr>
<tr>
  <td class="tr"><span class="ph">DH EH R W AH Z N</span><span class="wp">"there was n-"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n7/pair2/A_spk2416.mp3' | relative_url }}"></audio><span class="cap">spk 2416 · 0.40 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n7/pair2/B_spk4297.mp3' | relative_url }}"></audio><span class="cap">spk 4297 · 0.40 s</span></td>
</tr>
<tr>
  <td class="len" rowspan="2">14</td>
  <td class="tr"><span class="ph">DH IY Y UW N AY T IH D S T EY T S</span><span class="wp">"the united states"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n14/pair1/A_spk1271.mp3' | relative_url }}"></audio><span class="cap">spk 1271 · 0.98 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n14/pair1/B_spk454.mp3' | relative_url }}"></audio><span class="cap">spk 454 · 0.98 s</span></td>
</tr>
<tr>
  <td class="tr"><span class="ph">IH T W AH Z IH M P AA S AH B AH L</span><span class="wp">"it was impossible"</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n14/pair2/A_spk6269.mp3' | relative_url }}"></audio><span class="cap">spk 6269 · 0.94 s</span></td>
  <td><audio controls preload="none" src="{{ '/assets/pair-samples/phone_n14/pair2/B_spk7460.mp3' | relative_url }}"></audio><span class="cap">spk 7460 · 0.94 s</span></td>
</tr>
</tbody>
</table>
</div>
</div>

</div>

<p class="pub-venue" markdown="1">
The 10 LibriTTS speakers reserved for DiffVC's test set are excluded throughout.
Samples cut from LibriTTS (CC BY 4.0). Part of ongoing doctoral work on
domain-robust voice conversion. See the
[research overview]({{ '/research/#voice-conversion-domain-adaptation' | relative_url }}).
</p>
