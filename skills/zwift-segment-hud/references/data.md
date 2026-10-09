# Data contract

The renderer takes a local CSV and JSON config, not a URL. A Strava activity effort link can guide an agent in obtaining authorized data and matching boundaries. Fetching/authentication/FIT conversion are outside this release. Match activity identity, date/time, repeated passes, start/end GPS and elapsed duration. Keep pauses; do not substitute moving time. Respect the user's selected sports data provider.

CSV columns:

| Column | Unit / meaning |
| --- | --- |
| time_s | Segment elapsed seconds; 0,1,…,N including endpoint |
| distance_m | Metres from segment start; nondecreasing |
| lat, lon | Degrees |
| altitude_m | Metres |
| power_w | Watts, including recorded zeros |
| heart_rate_bpm | Beats per minute |
| cadence_rpm | Revolutions per minute |
| speed_m_s | Metres/second |
| ascent_m | Optional monotonic device cumulative ascent |

At least3 complete finite samples are required. Missing sensors/gaps, fractional-second effort duration and distance resets are not automatically repaired. Never turn missing sensor readings into zeros. Explain and document resampling if preparing data from another cadence. Without ascent_m, ascent is estimated as the sum of positive altitude changes.

```json
{
  "telemetry_path": "telemetry.csv",
  "route_display_name": "My Climb",
  "rider_name": "Rider",
  "rider_weight_kg": 70,
  "ftp_w": 250,
  "provenance": {
    "sports_source": "Your authorized data provider",
    "boundary_status": "verified",
    "boundary_evidence": "Describe how the effort was matched and cut"
  }
}
```

The numbers above are illustrative, not rider recommendations. Paths are relative to config. Optional font_path selects a local TTF/OTF (use a CJK font for Chinese text). Optional sector_end_distances_m lists1–12 increasing endpoints and must end at total distance. Automatic sectors use kilometre intervals, merge the tail and increase length for long courses.

3s power: trailing3 completed1Hz samples, including zero. W/kg uses the unrounded same mean. Cumulative averages exclude t0 and use completed samples. Sector means weight right-endpoint samples by interval overlap. Grade:10m grid,11-point smoothing, approximately100m centered elevation difference. These are display definitions, not new fitness estimates. Current averages do not read future samples; the last frame can show the exact endpoint without extending duration.

Keep real FIT/GPX, raw telemetry, private ride URLs and credentials outside version control. The demo is wholly synthetic, including its route.
