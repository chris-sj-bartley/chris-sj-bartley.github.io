---
layout: default
title: Voice conversion samples
description: >-
  Audio samples from a voice-conversion system evaluated across three
  conversion tasks: speaker identity (timbre), accent, and speaking style.
permalink: /samples/generated-samples/
---

<header class="page-header">
  <h1>Voice conversion samples</h1>
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
  table.gen-table { border-collapse: collapse; width: 100%; }
  .gen-table th, .gen-table td {
    padding: 0.5rem 0.6rem;
    text-align: left;
    vertical-align: middle;
    border-top: 1px solid rgba(128, 128, 128, 0.2);
  }
  .gen-table thead th {
    border-top: none;
    border-bottom: 2px solid rgba(128, 128, 128, 0.35);
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    opacity: 0.75;
    width: 33.33%;
  }
  .gen-table tr.cap-row td {
    border-top: 2px solid rgba(128, 128, 128, 0.4);
    padding: 0.6rem 0.6rem 0.1rem;
    font-size: 0.85em;
    font-style: italic;
    opacity: 0.65;
  }
  .gen-table tr.data-row td { padding-top: 0.15rem; }
  .gen-table .tag {
    display: block;
    font-size: 0.78em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    opacity: 0.7;
    margin-bottom: 0.25rem;
  }
  .gen-table audio { height: 34px; width: 100%; max-width: 240px; display: block; }
</style>

Samples from a voice-conversion system evaluated across three conversion tasks, each converting one attribute of a recording while keeping the spoken content fixed. For every example: <strong>Source</strong> is the original recording, <strong>Target reference</strong> is a real recording carrying the target attribute, and <strong>Generated</strong> is the model's conversion of the source content into that target. The italic line above each row is the source sentence, which the generated clip preserves.

<div class="samples" markdown="0">

<div class="sample-box">
<h3>Voice (timbre) conversion</h3>
<p class="box-sub">Converting a source speaker's voice into a different target speaker's voice, content unchanged. Source and target clips are from LibriTTS.</p>
<div class="table-wrap">
<table class="gen-table">
<thead>
<tr><th>Source</th><th>Target reference</th><th>Generated</th></tr>
</thead>
<tbody>
<tr class="cap-row"><td colspan="3">“If I should not be in, wait for me.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 2238</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000049_000000__to__5126/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5126</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000049_000000__to__5126/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5126</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000049_000000__to__5126/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“What is his name?”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 2238</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000061_000000__to__5126/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5126</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000061_000000__to__5126/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5126</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/2238_121415_000061_000000__to__5126/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“In the old days she had dressed for her own sake to look pretty and be admired.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 5126</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5126_34483_000006_000001__to__5322/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5322</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5126_34483_000006_000001__to__5322/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 5322</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5126_34483_000006_000001__to__5322/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“'God willing I'll find a way to repay you,' he said, finishing his wine.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 5322</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5322_7680_000053_000000__to__8057/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 8057</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5322_7680_000053_000000__to__8057/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 8057</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/5322_7680_000053_000000__to__8057/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“Therefore it is necessary, by a final examination of their characteristics, to eliminate those features which are hostile to sociability.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 8534</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216564_000027_000003__to__6415/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 6415</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216564_000027_000003__to__6415/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 6415</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216564_000027_000003__to__6415/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“If public utility had interfered, that forest-the only one for miles around-would still be standing.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 8534</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000015_000011__to__8057/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 8057</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000015_000011__to__8057/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 8057</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000015_000011__to__8057/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“So the government thinks.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 8534</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000027_000005__to__6415/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 6415</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000027_000005__to__6415/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 6415</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000027_000005__to__6415/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“There are thousands of documents, even official documents, to prove this, if necessary.”</td></tr>
<tr class="data-row">
<td><span class="tag">Speaker 8534</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000043_000003__to__2238/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 2238</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000043_000003__to__2238/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Speaker 2238</span><audio controls preload="none" src="{{ '/assets/generated-samples/timbre/8534_216567_000043_000003__to__2238/gen.mp3' | relative_url }}"></audio></td>
</tr>
</tbody>
</table>
</div>
</div>

<div class="sample-box">
<h3>Accent conversion</h3>
<p class="box-sub">Converting a source speaker's regional accent into a different target accent, content unchanged. Source and target clips are VCTK recordings.</p>
<div class="table-wrap">
<table class="gen-table">
<thead>
<tr><th>Source</th><th>Target reference</th><th>Generated</th></tr>
</thead>
<tbody>
<tr class="cap-row"><td colspan="3">“She can scoop these things into three red bags, and we will go meet her Wednesday at the train station.”</td></tr>
<tr class="data-row">
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2ireland_047/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2ireland_047/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2ireland_047/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“When a man looks for something beyond his reach, his friends say he is looking for the pot of gold at the end of the rainbow.”</td></tr>
<tr class="data-row">
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2north_america_007/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">American</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2north_america_007/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">American</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2north_america_007/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“There is a solution, she believes.”</td></tr>
<tr class="data-row">
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2scotland_048/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2scotland_048/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/england2scotland_048/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“The rainbow is a division of white light into many beautiful colors.”</td></tr>
<tr class="data-row">
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2england_054/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2england_054/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2england_054/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“If the red of the second bow falls upon the green of the first, the result is to give a bow with an abnormally wide yellow band, since red and green light when mixed form yellow.”</td></tr>
<tr class="data-row">
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2scotland_041/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2scotland_041/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/ireland2scotland_041/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“The difference in the rainbow depends considerably upon the size of the drops, and the width of the colored band increases as the size of the drops increases.”</td></tr>
<tr class="data-row">
<td><span class="tag">American</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/north_america2scotland_043/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/north_america2scotland_043/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/north_america2scotland_043/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“It is a simple equation.”</td></tr>
<tr class="data-row">
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2england_055/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2england_055/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">English</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2england_055/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“When a man looks for something beyond his reach, his friends say he is looking for the pot of gold at the end of the rainbow.”</td></tr>
<tr class="data-row">
<td><span class="tag">Scottish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2ireland_045/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2ireland_045/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Irish</span><audio controls preload="none" src="{{ '/assets/generated-samples/accent/scotland2ireland_045/gen.mp3' | relative_url }}"></audio></td>
</tr>
</tbody>
</table>
</div>
</div>

<div class="sample-box">
<h3>Style conversion</h3>
<p class="box-sub">Converting a source speaking style (happy, sad, laughing, whisper, enunciated, default) into a different target style, content unchanged. Source and target clips are from Expresso.</p>
<div class="table-wrap">
<table class="gen-table">
<thead>
<tr><th>Source</th><th>Target reference</th><th>Generated</th></tr>
</thead>
<tbody>
<tr class="cap-row"><td colspan="3">“So, what was he really doing?”</td></tr>
<tr class="data-row">
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00367_sad2whisper/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Whisper</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00367_sad2whisper/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Whisper</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00367_sad2whisper/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“With exercising our first amendment rights?”</td></tr>
<tr class="data-row">
<td><span class="tag">Happy</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_happy2sad/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_happy2sad/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_happy2sad/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“With exercising our first amendment rights?”</td></tr>
<tr class="data-row">
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_sad2enunciated/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Enunciated</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_sad2enunciated/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Enunciated</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00373_sad2enunciated/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“Yes, I have the doctor's appointment and checking the coffee on my to do list.”</td></tr>
<tr class="data-row">
<td><span class="tag">Happy</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00374_happy2default/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Default</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00374_happy2default/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Default</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00374_happy2default/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“I was in Australia actually.”</td></tr>
<tr class="data-row">
<td><span class="tag">Laughing</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00378_laughing2default/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Default</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00378_laughing2default/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Default</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex01_00378_laughing2default/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“We did a movie called Desperados for Netflix last year.”</td></tr>
<tr class="data-row">
<td><span class="tag">Enunciated</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00377_enunciated2laughing/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Laughing</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00377_enunciated2laughing/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Laughing</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00377_enunciated2laughing/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“I'm nineteen and this is nineteen ninety eight.”</td></tr>
<tr class="data-row">
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00379_sad2laughing/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Laughing</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00379_sad2laughing/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Laughing</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex03_00379_sad2laughing/gen.mp3' | relative_url }}"></audio></td>
</tr>
<tr class="cap-row"><td colspan="3">“The Norsemen considered the rainbow as a bridge over which the gods passed from earth to their home in the sky.”</td></tr>
<tr class="data-row">
<td><span class="tag">Sad</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex04_00373_sad2enunciated/src.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Enunciated</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex04_00373_sad2enunciated/tgt.mp3' | relative_url }}"></audio></td>
<td><span class="tag">Enunciated</span><audio controls preload="none" src="{{ '/assets/generated-samples/style/ex04_00373_sad2enunciated/gen.mp3' | relative_url }}"></audio></td>
</tr>
</tbody>
</table>
</div>
</div>

</div>

<p class="pub-venue" markdown="1">
Part of ongoing doctoral work on domain-robust voice conversion. See the [project overview]({{ '/projects/' | relative_url }}), or the [cross-speaker pair corpora]({{ '/research/pair-corpora/' | relative_url }}) used to train the underlying diffusion voice-conversion model.
</p>
