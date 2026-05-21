import React, { useState, useEffect } from 'react';
import './App.css';
import { loadStripe } from '@stripe/stripe-js';
import { trackEvent, trackPageView } from './analytics';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 'pk_test_placeholder');

// -- Upcoming major races calendar --
const MAJOR_RACES = [
  // -- NATIONAL HUNT --
  { date: '2026-04-09', meeting: 'Aintree', name: 'Aintree Hurdle',             grade: 'G1',   type: 'NH',   distance: '2m4f',   purse: '\u00a3250,000',     notes: 'Champion Hurdle horses next \u2014 festival opener for top hurdlers' },
  { date: '2026-04-09', meeting: 'Aintree', name: "Manifesto Novices' Chase",   grade: 'G1',   type: 'NH',   distance: '2m1f',   purse: '\u00a3100,000',     notes: 'Arkle/Novices Chase graduates chase Grade 1 glory at Liverpool' },
  { date: '2026-04-09', meeting: 'Aintree', name: "Mersey Novices' Hurdle",     grade: 'G1',   type: 'NH',   distance: '2m4f',   purse: '\u00a3100,000',     notes: 'Top novice hurdlers step up after Cheltenham; Mullins usually loads up' },
  { date: '2026-04-10', meeting: 'Aintree', name: 'Liverpool Hurdle',           grade: 'G1',   type: 'NH',   distance: '3m1f',   purse: '\u00a3150,000',     notes: "Stayers' Hurdle horses rerouted \u2014 tests champion staying hurdlers" },
  { date: '2026-04-10', meeting: 'Aintree', name: "Mildmay Novices' Chase",     grade: 'G1',   type: 'NH',   distance: '3m1f',   purse: '\u00a3100,000',     notes: 'RSA/Brown Advisory graduates over the Mildmay fences' },
  { date: '2026-04-11', meeting: 'Aintree', name: 'Grand National',             grade: 'Hcap', type: 'NH',   distance: '4m2\u00bdf', purse: '\u00a31,000,000', notes: "The world's most famous race \u2014 30 fences, 40 runners", highlight: true },
  { date: '2026-04-11', meeting: 'Aintree', name: "Maghull Novices' Chase",     grade: 'G1',   type: 'NH',   distance: '2m',     purse: '\u00a3100,000',     notes: 'Two-mile novice championship at Liverpool \u2014 Arkle horses return' },
  { date: '2026-04-18', meeting: 'Ayr',     name: 'Scottish Grand National',   grade: 'G3',   type: 'NH',   distance: '4m',     purse: '\u00a3180,000',     notes: 'The Scottish equivalent of the National \u2014 testing marathon chase' },
  { date: '2026-04-29', meeting: 'Punchestown', name: 'Punchestown Champion Chase',  grade: 'G1', type: 'NH', distance: '2m',   purse: '\u20ac300,000', notes: 'Queen Mother Champion Chase re-match \u2014 Majborough expected to defend' },
  { date: '2026-04-30', meeting: 'Punchestown', name: 'Punchestown Gold Cup',         grade: 'G1', type: 'NH', distance: '3m1f', purse: '\u20ac300,000', notes: 'Grade 1 Gold Cup equivalent \u2014 Gaelic Warrior favourite after Cheltenham win', highlight: true },
  { date: '2026-05-01', meeting: 'Punchestown', name: 'Punchestown Champion Hurdle',  grade: 'G1', type: 'NH', distance: '2m',   purse: '\u20ac250,000', notes: 'Champion Hurdle horses head to Ireland for the season finale' },
  { date: '2026-05-01', meeting: 'Punchestown', name: 'World Series Hurdle',           grade: 'G1', type: 'NH', distance: '3m',   purse: '\u20ac200,000', notes: "Stayers' championship continues \u2014 Teahupoo expected to defend" },
  { date: '2026-05-02', meeting: 'Punchestown', name: 'Champion Bumper',               grade: 'G1', type: 'NH', distance: '2m',   purse: '\u20ac100,000', notes: 'Final Grade 1 NH bumper of the season' },
  // -- FLAT --
  { date: '2026-04-14', meeting: 'Newmarket', name: 'Craven Stakes',        grade: 'G3', type: 'Flat', distance: '1m',   purse: '\u00a380,000',    notes: 'Key Classic trial \u2014 opens the Flat season at HQ' },
  { date: '2026-05-02', meeting: 'Newmarket', name: '2000 Guineas',         grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3600,000',   notes: 'First colts Classic of the season \u2014 one of the original five', highlight: true },
  { date: '2026-05-03', meeting: 'Newmarket', name: '1000 Guineas',         grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3500,000',   notes: 'First fillies Classic \u2014 Newmarket straight on fast ground', highlight: true },
  { date: '2026-05-08', meeting: 'Chester',   name: 'Chester Vase',         grade: 'G3', type: 'Flat', distance: '1m4f', purse: '\u00a380,000',    notes: "Premier Derby trial on Chester's unique tight circuit" },
  { date: '2026-05-14', meeting: 'York',      name: 'Dante Stakes',         grade: 'G2', type: 'Flat', distance: '1m2f', purse: '\u00a3175,000',   notes: 'Most important Derby trial \u2014 last major stepping stone before Epsom' },
  { date: '2026-05-15', meeting: 'York',      name: 'Musidora Stakes',      grade: 'G3', type: 'Flat', distance: '1m2f', purse: '\u00a390,000',    notes: 'Key Oaks trial for fillies at York' },
  { date: '2026-06-05', meeting: 'Epsom',     name: 'Coronation Cup',       grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a3350,000',   notes: 'Older horses over the Derby course \u2014 Champion older middle-distance' },
  { date: '2026-06-05', meeting: 'Epsom',     name: 'The Oaks',             grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a3800,000',   notes: "Second Classic \u2014 fillies only over Epsom's undulating 1m4f", highlight: true },
  { date: '2026-06-06', meeting: 'Epsom',     name: 'The Derby',            grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a31,500,000', notes: "The greatest Flat race in the world \u2014 3yo colts & fillies over the Downs", highlight: true },
  { date: '2026-06-16', meeting: 'Royal Ascot', name: 'Queen Anne Stakes',          grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3600,000', notes: 'Royal Ascot opener \u2014 top milers on the straight mile', highlight: true },
  { date: '2026-06-16', meeting: 'Royal Ascot', name: "King's Stand Stakes",        grade: 'G1', type: 'Flat', distance: '5f',   purse: '\u00a3600,000', notes: "Premier sprint \u2014 world's best five-furlong horses clash" },
  { date: '2026-06-17', meeting: 'Royal Ascot', name: "Prince of Wales's Stakes",   grade: 'G1', type: 'Flat', distance: '1m2f', purse: '\u00a3900,000', notes: 'Mid-week showpiece \u2014 top older horses over ten furlongs', highlight: true },
  { date: '2026-06-17', meeting: 'Royal Ascot', name: "St James's Palace Stakes",   grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3600,000', notes: "Guineas re-match at Ascot \u2014 3yo colts over the round mile" },
  { date: '2026-06-18', meeting: 'Royal Ascot', name: 'Ascot Gold Cup',              grade: 'G1', type: 'Flat', distance: '2m4f', purse: '\u00a3700,000', notes: 'The staying championship \u2014 Gold Cup Day centrepiece', highlight: true },
  { date: '2026-06-18', meeting: 'Royal Ascot', name: 'Coronation Stakes',           grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3600,000', notes: "Fillies' Guineas graduates \u2014 round mile at Ascot in mid-summer" },
  { date: '2026-06-19', meeting: 'Royal Ascot', name: 'Commonwealth Cup',            grade: 'G1', type: 'Flat', distance: '6f',   purse: '\u00a3600,000', notes: '3yo sprint championship \u2014 hottest young sprinters of the season' },
  { date: '2026-06-20', meeting: 'Royal Ascot', name: 'Golden Jubilee Stakes',       grade: 'G1', type: 'Flat', distance: '6f',   purse: '\u00a3600,000', notes: 'Open sprint finale to Royal Ascot \u2014 global sprinters assemble' },
  { date: '2026-07-09', meeting: 'Sandown',   name: 'Eclipse Stakes',         grade: 'G1', type: 'Flat', distance: '1m2f', purse: '\u00a3750,000',   notes: 'Derby horses meet older Classic generation \u2014 midsummer championship', highlight: true },
  { date: '2026-07-25', meeting: 'Ascot',     name: 'King George VI & Queen Elizabeth Stakes', grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a31,000,000', notes: 'Mid-season championship \u2014 best horses of all ages over 1m4f', highlight: true },
  { date: '2026-07-29', meeting: 'Goodwood',  name: 'Sussex Stakes',          grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3600,000',   notes: 'Glorious Goodwood highlight \u2014 milers from all generations clash', highlight: true },
  { date: '2026-07-30', meeting: 'Goodwood',  name: 'Goodwood Cup',           grade: 'G1', type: 'Flat', distance: '2m',   purse: '\u00a3400,000',   notes: 'Staying championship at Goodwood \u2014 Gold Cup horses return' },
  { date: '2026-08-20', meeting: 'York',      name: 'Juddmonte International', grade: 'G1', type: 'Flat', distance: '1m2f', purse: '\u00a31,000,000', notes: 'Richest race in Britain \u2014 the definitive middle-distance championship', highlight: true },
  { date: '2026-08-20', meeting: 'York',      name: 'Yorkshire Oaks',          grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a3500,000',   notes: 'Top fillies and mares over 1m4f at York \u2014 Ebor Festival showpiece' },
  { date: '2026-08-21', meeting: 'York',      name: 'Nunthorpe Stakes',         grade: 'G1', type: 'Flat', distance: '5f',   purse: '\u00a3350,000',   notes: 'Sprint championship \u2014 five furlongs at York, all ages' },
  { date: '2026-09-12', meeting: 'Doncaster', name: 'St Leger',                grade: 'G1', type: 'Flat', distance: '1m6f', purse: '\u00a3500,000',   notes: 'The oldest Classic \u2014 final leg of the Triple Crown', highlight: true },
  { date: '2026-09-26', meeting: 'Newmarket', name: 'Sun Chariot Stakes',      grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a3350,000',   notes: 'Top fillies and mares over a mile on the Rowley Mile' },
  { date: '2026-10-03', meeting: 'Newmarket', name: 'Middle Park Stakes',      grade: 'G1', type: 'Flat', distance: '6f',   purse: '\u00a3250,000',   notes: 'Two-year-old sprint championship \u2014 Guineas market springs to life' },
  { date: '2026-10-03', meeting: 'Newmarket', name: 'Cheveley Park Stakes',    grade: 'G1', type: 'Flat', distance: '6f',   purse: '\u00a3250,000',   notes: '2yo fillies sprint championship \u2014 key Guineas trial' },
  { date: '2026-10-17', meeting: 'Ascot',     name: 'QIPCO Champion Stakes',             grade: 'G1', type: 'Flat', distance: '1m2f', purse: '\u00a31,300,000', notes: 'Season finale \u2014 the definitive autumn championship at British Champions Day', highlight: true },
  { date: '2026-10-17', meeting: 'Ascot',     name: 'Queen Elizabeth II Stakes',         grade: 'G1', type: 'Flat', distance: '1m',   purse: '\u00a31,100,000', notes: "Milers' Championship on Champions Day \u2014 season finale for mile stars", highlight: true },
  { date: '2026-10-17', meeting: 'Ascot',     name: 'British Champions Sprint',          grade: 'G1', type: 'Flat', distance: '6f',   purse: '\u00a3700,000',   notes: "Sprint Championship \u2014 season finale for Britain's best sprinters" },
  { date: '2026-10-17', meeting: 'Ascot',     name: 'British Champions Fillies & Mares', grade: 'G1', type: 'Flat', distance: '1m4f', purse: '\u00a3700,000',   notes: 'Fillies and mares season finale' },
];

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

function daysUntil(dateStr) {
  const today = new Date(); today.setHours(0,0,0,0);
  const diff = Math.round((new Date(dateStr + 'T00:00:00') - today) / 86400000);
  if (diff < 0) return null;
  if (diff === 0) return 'TODAY';
  if (diff === 1) return 'Tomorrow';
  return diff + ' days';
}

function isPast(dateStr) {
  const today = new Date(); today.setHours(0,0,0,0);
  return new Date(dateStr + 'T00:00:00') < today;
}

function groupByMeeting(races) {
  const meetings = {};
  races.forEach(r => {
    const key = r.date + '__' + r.meeting;
    if (!meetings[key]) meetings[key] = { date: r.date, meeting: r.meeting, races: [] };
    meetings[key].races.push(r);
  });
  return Object.values(meetings).sort((a,b) => a.date.localeCompare(b.date));
}

function getNextMajorMeetingTarget() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const upcoming = MAJOR_RACES
    .filter((race) => {
      const raceDate = new Date(race.date + 'T00:00:00');
      return raceDate >= today;
    })
    .sort((a, b) => a.date.localeCompare(b.date));

  if (!upcoming.length) return null;
  return { date: upcoming[0].date, meeting: upcoming[0].meeting };
}

function buildFeaturedMeetingTabLabel(meeting, dateStr) {
  if (!meeting) return 'Featured Meet';
  if (!dateStr) return meeting;
  const d = new Date(dateStr + 'T12:00:00');
  const weekday = d.toLocaleDateString('en-GB', { weekday: 'short' });
  const month = d.toLocaleDateString('en-GB', { month: 'short' });
  const day = d.toLocaleDateString('en-GB', { day: 'numeric' });
  return `${meeting} ${weekday} ${month} ${day}`;
}

// ---- Pick best key reasons from selection_reasons ----
// Returns top N reasons: non-generic first, sorted by pts value
function bestKeyReasons(reasons, n = 2) {
  if (!Array.isArray(reasons) || reasons.length === 0) return [];
  const parsePts = r => { const m = r.match(/:\s*([+-]?\d+(?:\.\d+)?)\s*pts?/i); return m ? Math.abs(parseFloat(m[1])) : 0; };
  const isGeneric = r => /sweet spot|near optimal odds|short odds|long shot|\d+[-–]\d+\s*odds/i.test(r);
  const sorted = [...reasons].sort((a, b) => {
    const ag = isGeneric(a) ? 1 : 0, bg = isGeneric(b) ? 1 : 0;
    if (ag !== bg) return ag - bg;
    return parsePts(b) - parsePts(a);
  });
  return sorted.slice(0, n).map(r => r.replace(/:\s*[+-]?\d+(?:\.\d+)?\s*pts?/i, '').trim());
}

// Derive readable reasons from score_breakdown when selection_reasons is empty
const SB_LABELS = {
  going_suitability:    'Proven suited to today\'s going',
  cd_bonus:             'Course & distance winner',
  course_performance:   'Strong course record',
  total_wins:           'Multiple career wins',
  market_leader:        'Market leader (lowest odds)',
  jockey_quality:       'Top-quality jockey booking',
  jockey_course_bonus:  'Jockey excels at this course',
  trainer_course_bonus: 'Trainer excels at this course',
  market_steam:         'Market steam — money coming in',
  timeform_stars:       'Timeform star rating',
  distance_suitability: 'Proven at today\'s distance',
  consistency:          'Highly consistent performer',
  deep_form:            'Strong deep form',
  recent_win:           'Recent win in form',
  database_history:     'Strong historical record here',
  bounce_back:          'Due a bounce-back run',
  meeting_focus:        'Trainer targeting this meeting',
  unexposed_bonus:      'Lightly-raced & unexposed',
  age_bonus:            'Ideal peak racing age',
  optimal_odds:         'Near-optimal betting odds',
  sweet_spot:           'Odds in the model\'s sweet spot',
};
function reasonsFromBreakdown(sb, n = 2) {
  if (!sb || typeof sb !== 'object') return [];
  const generic = new Set(['sweet_spot','optimal_odds']);
  const entries = Object.entries(sb)
    .filter(([, v]) => parseFloat(v) > 0)
    .sort((a, b) => {
      const ag = generic.has(a[0]) ? 1 : 0, bg = generic.has(b[0]) ? 1 : 0;
      if (ag !== bg) return ag - bg;
      return parseFloat(b[1]) - parseFloat(a[1]);
    });
  return entries.slice(0, n).map(([k]) => SB_LABELS[k] || k.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase()));
}

// Parse UTC race_time string and display in BST (Europe/Dublin)
function fmtUtcTime(rt) {
  if (!rt) return '';
  const s = rt.length <= 16 ? rt + ':00Z' : (rt.endsWith('Z') || rt.includes('+') ? rt : rt + 'Z');
  const d = new Date(s);
  return isNaN(d) ? rt.substring(11,16) : d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Europe/Dublin'});
}

function bettingWindow(pick, now) {
  const odds  = parseFloat(pick.odds || 0);
  const sb    = pick.score_breakdown || {};
  const isML  = Number(pick.market_rank || 99) === 1 || parseFloat(sb.market_leader || 0) > 0;

  // Time to race in minutes
  let mins = null;
  if (pick.race_time) {
    try {
      const rawRt = pick.race_time || '';
      const rt = new Date(!rawRt.endsWith('Z') && !rawRt.includes('+') ? rawRt + 'Z' : rawRt);
      if (!isNaN(rt)) mins = Math.round((rt - now) / 60000);
    } catch {}
  }

  // Already past or within 15 mins — urgent
  if (mins !== null && mins <= 15 && mins >= -10) {
    return { label:'⏰ Bet Now', desc:'Race imminent', color:'#dc2626', bg:'#fef2f2', border:'#fca5a5' };
  }
  // Within 90 mins + short price — get in before it goes
  if (mins !== null && mins <= 90 && odds > 0 && odds <= 3.0) {
    return { label:'⏰ Bet Now', desc:'Short price + race soon', color:'#dc2626', bg:'#fef2f2', border:'#fca5a5' };
  }
  // Odds-on — price will only shorten
  if (odds > 0 && odds <= 1.8) {
    return { label:'⚡ Bet Early', desc:'Odds-on — lock in before it shortens', color:'#d97706', bg:'#fffbeb', border:'#fcd34d' };
  }
  // Up to 2/1 and market leader — sharp money will move it
  if (odds > 0 && odds <= 3.0 && isML) {
    return { label:'⚡ Bet Early', desc:'Market leader — sharp money expected', color:'#d97706', bg:'#fffbeb', border:'#fcd34d' };
  }
  // Sweet spot 2/1–5/1 — 1-2 hrs before is fine
  if (odds > 0 && odds <= 6.0) {
    return { label:'🕐 1-2hrs Before', desc:'Price stable until near off', color:'#059669', bg:'#f0fdf4', border:'#a7f3d0' };
  }
  return { label:'📅 Anytime Today', desc:'Long price — odds stable', color:'#6b7280', bg:'#f9fafb', border:'#e5e7eb' };
}

// ---- Race Intel summary generator ----
function raceIntelSummary(pick, now) {
  const sb        = pick.score_breakdown || {};
  const allHorses = pick.all_horses || [];
  const ourScore  = parseFloat(pick.score || pick.comprehensive_score || 0);
  const ourHorse  = (pick.horse || '').toLowerCase();
  // Last analysed time
  const analysedAt = pick.updated_at || pick.created_at || null;
  let analysedStr = null, freshness = null, freshnessOk = true;
  if (analysedAt) {
    const analysedDate = new Date(analysedAt);
    const minsAgo      = Math.round(((now || new Date()) - analysedDate) / 60000);
    analysedStr = minsAgo < 60
      ? `${minsAgo} min ago`
      : `${Math.floor(minsAgo / 60)}h ${minsAgo % 60}m ago`;

    // Gap between last analysis and race start
    // Parse race_time as UTC (bare ISO strings have no tz — treat as UTC)
    const raceDate = pick.race_time ? (() => { const _rt = pick.race_time; return new Date(!_rt.endsWith('Z') && !_rt.includes('+') ? _rt + 'Z' : _rt); })() : null;
    if (!isNaN(raceDate)) {
      const gapMins = Math.round((raceDate - analysedDate) / 60000);
      const h = Math.floor(gapMins / 60);
      const m = gapMins % 60;
      // How far is the race from NOW (not from analysis time)
      const minsToRace = Math.round((raceDate - (now || new Date())) / 60000);
      const analysisAgeHours = minsAgo / 60;

      if (minsToRace <= 0) {
        freshness = 'Race started';
        freshnessOk = false;
      } else if (minsToRace <= 30 && analysisAgeHours >= 2) {
        // Within 30 mins of race but analysis is >2h old — flag as stale
        freshness = `⚠ Last check ${Math.floor(analysisAgeHours)}h ago — re-run soon`;
        freshnessOk = false;
      } else if (gapMins <= 0) {
        freshness = 'Analysis after race start';
        freshnessOk = false;
      } else if (gapMins <= 30) {
        freshness = `✓ Final check: ${gapMins}min before race`;
        freshnessOk = true;
      } else if (gapMins <= 120) {
        freshness = `${gapMins}min before race`;
      } else {
        freshness = `${h}h ${m > 0 ? m + 'm' : ''} before race`.trim();
      }
    }
  }

  // Main rival
  const sorted  = [...allHorses].sort((a, b) => parseFloat(b.score||0) - parseFloat(a.score||0));
  const rival   = sorted.find(h => (h.horse||'').toLowerCase() !== ourHorse);
  const rivalGap = rival ? (ourScore - parseFloat(rival.score||0)).toFixed(0) : null;

  // Key edge from score_breakdown (top non-generic positive factor)
  const generic  = new Set(['sweet_spot', 'optimal_odds']);
  const topFactor = Object.entries(sb)
    .filter(([k, v]) => !generic.has(k) && parseFloat(v) > 0)
    .sort((a, b) => parseFloat(b[1]) - parseFloat(a[1]))[0];
  const keyEdge  = topFactor ? (SCORE_LABELS[topFactor[0]] || topFactor[0].replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase())) + ` (+${parseFloat(topFactor[1]).toFixed(0)}pts)` : null;

  // Risk flag
  const penaltyTotal = Object.entries(sb).filter(([,v]) => parseFloat(v) < 0).reduce((s,[,v]) => s + parseFloat(v), 0);
  let riskStr = null;
  if (rivalGap !== null && parseInt(rivalGap) <= 3) riskStr = `Tight race — ${rival.horse} only ${rivalGap}pt${rivalGap==='1'?'':'s'} behind`;
  else if (penaltyTotal < -5) riskStr = `Penalty flags applied (${penaltyTotal.toFixed(0)}pts deducted)`;

  return { analysedStr, freshness, freshnessOk, keyEdge, rival, rivalGap, riskStr };
}

// ---- Decimal → Fractional odds converter ----
function toFractional(decimal) {
  if (!decimal) return '';
  const d = parseFloat(decimal);
  if (isNaN(d) || d <= 1.0) return 'SP';
  const tbl = [
    [1.07,'1/14'],[1.09,'1/11'],[1.11,'1/9'],[1.13,'1/8'],[1.17,'1/6'],
    [1.20,'1/5'],[1.25,'1/4'],[1.29,'2/7'],[1.33,'1/3'],[1.36,'4/11'],
    [1.40,'2/5'],[1.44,'4/9'],[1.50,'1/2'],[1.53,'8/15'],[1.57,'4/7'],
    [1.62,'4/6'],[1.67,'2/3'],[1.72,'8/11'],[1.80,'4/5'],[1.91,'10/11'],
    [2.00,'EVS'],[2.10,'11/10'],[2.20,'6/5'],[2.25,'5/4'],[2.38,'11/8'],
    [2.50,'6/4'],[2.63,'13/8'],[2.75,'7/4'],[2.88,'15/8'],[3.00,'2/1'],
    [3.25,'9/4'],[3.38,'19/8'],[3.50,'5/2'],[3.75,'11/4'],[4.00,'3/1'],
    [4.33,'10/3'],[4.50,'7/2'],[5.00,'4/1'],[5.50,'9/2'],[6.00,'5/1'],
    [6.50,'11/2'],[7.00,'6/1'],[7.50,'13/2'],[8.00,'7/1'],[8.50,'15/2'],
    [9.00,'8/1'],[9.50,'17/2'],[10.0,'9/1'],[11.0,'10/1'],[12.0,'11/1'],
    [13.0,'12/1'],[14.0,'13/1'],[15.0,'14/1'],[17.0,'16/1'],[21.0,'20/1'],
    [26.0,'25/1'],[34.0,'33/1'],[51.0,'50/1'],[101.0,'100/1'],
  ];
  let best = tbl[0], bestDiff = Math.abs(d - tbl[0][0]);
  for (const [dec, frac] of tbl) {
    const diff = Math.abs(d - dec);
    if (diff < bestDiff) { bestDiff = diff; best = [dec, frac]; }
  }
  if (bestDiff / d <= 0.08) return best[1];
  // fallback: compute nearest simple fraction
  const n = Math.round((d - 1) * 20);
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  const g = gcd(n, 20);
  return `${n/g}/${20/g}`;
}

function LegalDisclaimerCard({ style }) {
  return (
    <div style={{ marginTop: '28px', background: 'rgba(245,158,11,0.10)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: '10px', padding: '12px 16px', ...style }}>
      <div style={{ color: '#fbbf24', fontSize: '13px', fontWeight: '800', marginBottom: '4px' }}>Important Legal Disclaimer</div>
      <div style={{ color: 'rgba(255,255,255,0.70)', fontSize: '12px', lineHeight: '1.65' }}>
        BetBudAI is a research and education platform only. It is not a betting site, not a bookmaker, and not gambling or financial advice.
        Performance, ROI, examples, and selections are informational and never guaranteed. Markets and outcomes can change after publication.
        You are solely responsible for all betting decisions. Bet responsibly, set strict limits, and do not gamble with money you cannot afford to lose.
      </div>
    </div>
  );
}

function isRaceInFuture(pick) {
  const rawRaceTime = (pick?.race_time || '').toString().trim();
  if (!rawRaceTime) return false;
  try {
    let iso = rawRaceTime.includes('T') ? rawRaceTime : rawRaceTime.replace(' ', 'T');
    if (!iso.endsWith('Z') && !iso.includes('+')) iso += 'Z';
    const raceDate = new Date(iso);
    return !isNaN(raceDate.getTime()) && raceDate.getTime() > Date.now();
  } catch {
    return false;
  }
}

function normalizePickOutcome(pick) {
  const outcome = (pick?.outcome || '').toLowerCase();
  const emoji = (pick?.result_emoji || '').trim();
  if (outcome === 'win' || outcome === 'won' || emoji === '\u2705') return 'WIN';
  if (outcome === 'placed' || emoji === '\ud83d\udd35') return 'PLACED';
  if (outcome === 'loss' || outcome === 'lost' || emoji === '\u274c') {
    if (isRaceInFuture(pick)) return '';
    return 'LOSS';
  }
  return '';
}

function renderScoreGapBadge(scoreGap) {
  const gap = Number(scoreGap);
  if (!Number.isFinite(gap) || gap <= 0) return null;

  const roundedGap = Math.round(gap);
  const unit = roundedGap === 1 ? 'pt' : 'pts';

  return (
    <span style={{ background:'#f0fdf4', border:'1px solid #86efac', borderRadius:'5px', padding:'2px 8px', fontSize:'12px', color:'#166534', fontWeight:'700' }}>
      +{roundedGap} {unit} clear of field
    </span>
  );
}

function buildPositiveBannerData(latestWinner, yesterdaySummary, yesterdayPicks, yesterdayDateValue) {
  const summary = yesterdaySummary || {};
  const picks = Array.isArray(yesterdayPicks) ? yesterdayPicks : [];

  const wins = Number(summary.wins || 0);
  const places = Number(summary.places || 0);
  const total = Number(summary.total_picks || 0);
  const hasPositiveYesterday = (wins + places) > 0;

  const winnerFromYesterday = picks
    .filter(p => normalizePickOutcome(p) === 'WIN')
    .sort((a, b) => {
      const oddsA = Number(a?.sp_odds || a?.odds || 0);
      const oddsB = Number(b?.sp_odds || b?.odds || 0);
      return oddsB - oddsA;
    })[0];
  const horse = winnerFromYesterday?.horse || latestWinner?.horse || '';
  const odds =
    winnerFromYesterday?.fractional_odds ||
    toFractional(winnerFromYesterday?.sp_odds || winnerFromYesterday?.odds) ||
    latestWinner?.fractional_odds ||
    '';
  const label = hasPositiveYesterday ? 'yesterday' : (latestWinner?.label || 'recently');

  const yesterdayDate = yesterdayDateValue
    ? new Date(`${yesterdayDateValue}T12:00:00Z`)
    : (() => {
        const d = new Date();
        d.setDate(d.getDate() - 1);
        return d;
      })();
  const yesterdayLabel = yesterdayDate.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });

  let summaryMode = 'generic';
  let summaryText = 'Positive news: today\'s strongest value picks are now highlighted by the model.';
  if (hasPositiveYesterday && total > 0) {
    summaryMode = 'yesterday';
    summaryText = `Yesterday (${yesterdayLabel}): ${wins} winner${wins === 1 ? '' : 's'} & ${places} placed out of ${total}.`;
  } else if (latestWinner?.horse && latestWinner?.fractional_odds) {
    summaryMode = 'recent';
    summaryText = 'Previous days: momentum remains positive with recent value winners landing.';
  }

  return {
    horse,
    odds,
    label,
    yesterdayLabel,
    summaryMode,
    summaryText,
  };
}

// ---- App ----
function App() {
  const [page, setPage] = useState('home');
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);
  const [accountSettingsRequest, setAccountSettingsRequest] = useState(null);
  const [featuredMeetingMeta, setFeaturedMeetingMeta] = useState(null);

  const navigateToPage = (nextPage, eventParams = null) => {
    if (eventParams) trackEvent('navigation_click', eventParams);
    setPage(nextPage);
  };

  // ── Authentication state ──────────────────────────────────────────────────
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try { return !!localStorage.getItem('betbudai_user'); } catch { return false; }
  });
  const [authUser, setAuthUser] = useState(() => {
    try { const u = localStorage.getItem('betbudai_user'); return u ? JSON.parse(u) : null; } catch { return null; }
  });

  // ── Email verification via ?verify= query param ───────────────────────────
  const [verifyState, setVerifyState] = useState(null); // null | 'loading' | {success,message,user} | {success:false,error}

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('settings') !== 'account') return;
    setAccountSettingsRequest({
      email: params.get('email') || '',
      token: params.get('token') || '',
    });
    if (isAuthenticated) setPage('account');
    window.history.replaceState({}, '', window.location.pathname);
  }, [isAuthenticated]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token  = params.get('verify');
    if (!token) return;
    setVerifyState('loading');
    fetch(`${API_BASE_URL}/api/verify-email?token=${encodeURIComponent(token)}`)
      .then(r => r.json())
      .then(data => {
        setVerifyState(data);
        if (data.success && data.user) {
          try { localStorage.setItem('betbudai_user', JSON.stringify(data.user)); } catch {}
          setAuthUser(data.user);
          setIsAuthenticated(true);
        }
        // Clean the token from the URL without triggering a refresh
        window.history.replaceState({}, '', window.location.pathname);
      })
      .catch(() => setVerifyState({ success: false, error: 'Network error during verification. Please try again.' }));
  }, []);

  // ── Handle Stripe payment redirect (?payment=success&tier=...) ────────────
  const [paymentSuccess, setPaymentSuccess] = useState(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const payment = params.get('payment');
    const tier = params.get('tier');
    if (payment === 'success' && tier) {
      trackEvent('subscription_started', {
        tier,
        source: 'stripe_redirect',
      });
      setPaymentSuccess(tier);
      // Refresh user data from backend to get updated subscription_tier
      if (authUser?.email) {
        fetch(`${API_BASE_URL}/api/subscription-status`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authUser.email })
        })
          .then(r => r.json())
          .then(data => {
            if (data.subscription_tier) {
              const updatedUser = { ...authUser, role: data.subscription_tier, subscription_tier: data.subscription_tier, subscription_status: data.subscription_status };
              try { localStorage.setItem('betbudai_user', JSON.stringify(updatedUser)); } catch {}
              setAuthUser(updatedUser);
            }
          })
          .catch(() => {});
      }
      window.history.replaceState({}, '', window.location.pathname);
      setTimeout(() => setPaymentSuccess(null), 8000);
    } else if (payment === 'cancelled') {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const featuredMeetingTitle = featuredMeetingMeta?.pageTitle || featuredMeetingMeta?.tabLabel || 'Featured Meet';

  useEffect(() => {
    const pageTitles = {
      home: 'Home',
      pricing: 'Pricing',
      picks: 'Daily Picks',
      picks5: 'Top 5 Picks',
      majors: featuredMeetingTitle || 'Featured Meet',
      laythe: 'VIP Rollers',
      account: 'My Account',
      admin: 'Admin',
      yesterday: 'Latest Results',
    };

    trackPageView(page, {
      page_title: pageTitles[page] || page,
      page_path: `/${page}`,
      user_status: isAuthenticated ? 'authenticated' : 'guest',
    });

    if (page === 'pricing') {
      trackEvent('view_pricing', {
        source: 'page_navigation',
        user_status: isAuthenticated ? 'authenticated' : 'guest',
      });
    }
  }, [page, isAuthenticated, featuredMeetingTitle]);

  const handleAuthSuccess = (userData) => {
    const userRole = (userData?.role || '').toLowerCase();
    const hasTrialAccess = userData?.subscription_status === 'trialing';
    const hasActiveSub = ['trialing', 'active', 'canceling'].includes(userData?.subscription_status);
    const hasPaidAccess = hasTrialAccess || userRole === 'admin' || userRole === 'premium' || userRole === 'vip' ||
      ((userData?.subscription_tier === 'premium' || userData?.subscription_tier === 'vip') && hasActiveSub);
    try { localStorage.setItem('betbudai_user', JSON.stringify(userData)); } catch {}
    setAuthUser(userData);
    setIsAuthenticated(true);
    if (hasPaidAccess) {
      navigateToPage(accountSettingsRequest ? 'account' : 'picks5');
    } else {
      navigateToPage('home');
    }
  };

  const handleLogout = () => {
    try { localStorage.removeItem('betbudai_user'); } catch {}
    setAuthUser(null);
    setIsAuthenticated(false);
    navigateToPage('home');
  };

  const handleTabClick = (key) => {
    // Guests can access Home and Featured Meeting only.
    if (!isAuthenticated && key !== 'home' && key !== 'punchestown') {
      navigateToPage('home', { destination: 'home' });
      return;
    }

    // Allow navigation; entitlement checks also happen at content level.
    navigateToPage(key, { destination: key });
  };

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadFeaturedMeetingMeta = async () => {
      try {
        const params = new URLSearchParams();
        const response = await fetch(`${API_BASE_URL}/api/picks/featured-meeting?${params.toString()}`, {
          cache: 'default',
          headers: { 'Cache-Control': 'max-age=300' }
        });
        const data = await response.json();
        if (!cancelled && data?.success) {
          const effectiveMeeting = data.course;
          const effectiveDate = data.date || new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
          const meetingLabel = buildFeaturedMeetingTabLabel(effectiveMeeting, effectiveDate);
          setFeaturedMeetingMeta({
            course: effectiveMeeting,
            tabLabel: 'Featured Meet',
            subLabel: meetingLabel,
            pageTitle: 'Featured Meet',
            date: effectiveDate,
          });
        }
      } catch {
        if (!cancelled) setFeaturedMeetingMeta(null);
      }
    };

    loadFeaturedMeetingMeta();
    const interval = setInterval(loadFeaturedMeetingMeta, 15 * 60 * 1000);

    const onVisibilityOrFocus = () => {
      if (!cancelled) loadFeaturedMeetingMeta();
    };
    document.addEventListener('visibilitychange', onVisibilityOrFocus);
    window.addEventListener('focus', onVisibilityOrFocus);

    return () => {
      cancelled = true;
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisibilityOrFocus);
      window.removeEventListener('focus', onVisibilityOrFocus);
    };
  }, []);

  useEffect(() => {
    const title = page === 'punchestown'
      ? featuredMeetingTitle
      : 'BetBudAI — AI Horse Racing Picks';
    document.title = title;

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute('content', title);
    const twitterTitle = document.querySelector('meta[name="twitter:title"]');
    if (twitterTitle) twitterTitle.setAttribute('content', title);
  }, [page, featuredMeetingTitle]);

  const isAdmin = authUser?.role === 'admin';
  const hasExplicitFreeRole = (authUser?.role || '').toLowerCase() === 'free';
  const hasActivePaidStatus = ['trialing', 'active', 'canceling'].includes(authUser?.subscription_status);
  const hasTrialAccess = isAuthenticated && authUser?.subscription_status === 'trialing';
  const hasPaidEntitlement = isAuthenticated && (
    hasTrialAccess ||
    (
      !hasExplicitFreeRole &&
      (
        authUser?.role === 'admin' ||
        authUser?.role === 'premium' ||
        authUser?.role === 'vip' ||
        (
          (authUser?.subscription_tier === 'premium' || authUser?.subscription_tier === 'vip') &&
          hasActivePaidStatus
        )
      )
    )
  );
  const hasVipEntitlement = isAuthenticated && (
    (hasTrialAccess && authUser?.subscription_tier === 'vip') ||
    (
      !hasExplicitFreeRole &&
      (
        authUser?.role === 'admin' ||
        authUser?.role === 'vip' ||
        (authUser?.subscription_tier === 'vip' && hasActivePaidStatus)
      )
    )
  );
  const isFreeUser = isAuthenticated && (hasExplicitFreeRole || !hasPaidEntitlement);
  const isLockedPaidUser = isAuthenticated && (hasExplicitFreeRole || !hasPaidEntitlement);
  const isLockedVipUser = isAuthenticated && !hasVipEntitlement;
  const isPremium = authUser?.role === 'premium' || authUser?.role === 'vip' || authUser?.role === 'admin';
  const isVip = authUser?.role === 'vip' || authUser?.role === 'admin';
  const isHomeOnlyUser = !isAuthenticated || (!isAdmin && !hasPaidEntitlement);

  return (
    <div className="App">
      <header className="App-header">
        <h1>BetBudAI.com</h1>
        <p style={{ fontSize: '14px', opacity: 0.8, margin: '4px 0 0' }}>AI-powered racing analysis · UK &amp; Ireland</p>
        {isAuthenticated && (
          <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', color: '#34d399', fontWeight: '600' }}>
              ✓ Signed in as <strong>{authUser?.username || authUser?.email}</strong>
            </span>
            <button onClick={handleLogout} style={{
              background: 'none', border: '1px solid rgba(255,255,255,0.25)', borderRadius: '6px',
              color: 'rgba(255,255,255,0.55)', fontSize: '11px', padding: '3px 10px', cursor: 'pointer',
            }}>Sign out</button>
          </div>
        )}
      </header>

      {/* ── Email verification banner ─────────────────────────────────── */}
      {verifyState === 'loading' && (
        <div style={{ textAlign:'center', padding:'20px', background:'rgba(5,150,105,0.12)', borderBottom:'1px solid rgba(52,211,153,0.2)', color:'#34d399', fontSize:'15px' }}>
          ⏳ Verifying your email address…
        </div>
      )}
      {verifyState && verifyState !== 'loading' && verifyState.success && (
        <div style={{ textAlign:'center', padding:'16px 24px', background:'rgba(5,150,105,0.15)', borderBottom:'1px solid rgba(52,211,153,0.3)', color:'#34d399', fontSize:'15px', fontWeight:'600' }}>
          ✅ Email verified! Welcome to BetBudAI, <strong>{verifyState.user?.username || verifyState.user?.email}</strong>. You're now signed in.
        </div>
      )}
      {verifyState && verifyState !== 'loading' && !verifyState.success && (
        <div style={{ textAlign:'center', padding:'16px 24px', background:'rgba(239,68,68,0.12)', borderBottom:'1px solid rgba(239,68,68,0.3)', color:'#f87171', fontSize:'14px' }}>
          ⚠ {verifyState.error}
        </div>
      )}

      <div style={{ display:'flex', justifyContent: isMobile ? 'flex-start' : 'center', gap: isMobile ? '8px' : '12px', marginBottom: isMobile ? '20px' : '32px', flexWrap: isMobile ? 'nowrap' : 'wrap', overflowX: isMobile ? 'auto' : 'visible', WebkitOverflowScrolling: 'touch', padding: isMobile ? '0 8px 8px' : '0', msOverflowStyle: 'none', scrollbarWidth: 'none' }}>
        {[
          { key:'home',      label:'Home',             emoji:'🏠', sub:'About & sign in',     gated: false, tierRequired: null },
          { key:'picks5',    label:'Daily Picks',      emoji:'🏆', sub:'4+ tips daily',       gated: true, tierRequired: 'premium' },
          { key:'punchestown', label: featuredMeetingMeta?.tabLabel || 'Featured Meet', emoji:'🐎', sub: featuredMeetingMeta?.subLabel || '2 watchlist selections', gated: false, tierRequired: null },
          { key:'yesterday', label:'All Results',      emoji:'📊', sub:'Live ROI tracking',    gated: true, tierRequired: 'premium' },
          { key:'laythe',    label:'VIP Rollers',      emoji:'👑', sub:'Lay the Favourite',   gated: true, tierRequired: 'vip' },
          { key:'majors',    label:'Major Races',      emoji:'🏆', sub:'Ante-post + previews', gated: true, tierRequired: 'premium' },
          ...(isAuthenticated ? [{ key:'account', label:'My Account', emoji:'👤', sub:'Profile & billing', gated: true, tierRequired: 'premium' }] : []),
          ...(isAdmin ? [{ key:'admin', label:'Admin', emoji:'⚙️', sub:'System controls', gated: true, admin: true, tierRequired: 'admin' }] : []),
        ]
          .filter(tab => {
            // Show all tabs to everyone except admin (admin only for admins)
            if (tab.admin && !isAdmin) return false;
            return true;
          })
          .map(tab => {
          const locked =
            (tab.gated && !isAuthenticated) ||
            (tab.tierRequired === 'premium' && !hasPaidEntitlement) ||
            (tab.tierRequired === 'vip' && !hasVipEntitlement) ||
            (tab.tierRequired === 'admin' && !isAdmin);
          const isActive = page === tab.key;
          return (
            <button key={tab.key} onClick={() => handleTabClick(tab.key)} style={{
              background: locked
                ? 'rgba(255,255,255,0.04)'
                : tab.admin
                  ? (isActive ? 'linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%)' : 'rgba(124,58,237,0.18)')
                  : tab.key==='laythe'
                    ? (isActive ? 'linear-gradient(135deg,#d97706 0%,#b45309 100%)' : 'rgba(217,119,6,0.18)')
                    : (isActive ? 'linear-gradient(135deg,#059669 0%,#047857 100%)' : 'rgba(255,255,255,0.12)'),
              border: locked
                ? '2px solid rgba(255,255,255,0.1)'
                : tab.admin
                  ? (isActive ? '2px solid #a78bfa' : '2px solid rgba(167,139,250,0.4)')
                  : tab.key==='laythe'
                    ? (isActive ? '2px solid #f59e0b' : '2px solid rgba(245,158,11,0.4)')
                    : (isActive ? '2px solid #10b981' : '2px solid rgba(255,255,255,0.25)'),
              borderRadius:'10px', color: locked ? 'rgba(255,255,255,0.3)' : 'white',
              cursor: 'pointer',
              padding: isMobile ? '8px 10px' : '12px 24px',
              minWidth: isMobile ? 'auto' : '140px',
              flex: isMobile ? '0 0 auto' : undefined,
              textAlign:'center', transition:'all 0.2s', opacity: locked ? 0.5 : 1,
            }}>
              <div style={{ fontSize: isMobile ? '13px' : '16px', fontWeight:'700', whiteSpace:'nowrap' }}>
                {locked ? '🔒' : tab.emoji} {tab.label}
              </div>
              {!isMobile && <div style={{ fontSize:'11px', opacity:0.75, marginTop:'2px' }}>
                {locked ? (isAuthenticated ? 'Upgrade to access' : 'Sign in to access') : tab.sub}
              </div>}
            </button>
          );
        })}
      </div>

      <main style={{ maxWidth:'960px', margin:'0 auto', padding:'0 12px' }}>
        {paymentSuccess && (
          <div style={{ background:'linear-gradient(135deg,rgba(52,211,153,0.2),rgba(16,185,129,0.15))', border:'1.5px solid rgba(52,211,153,0.5)', borderRadius:'12px', padding:'16px 20px', textAlign:'center', marginBottom:'16px' }}>
            <div style={{ fontSize:'20px', marginBottom:'4px' }}>🎉</div>
            <div style={{ fontSize:'16px', fontWeight:'800', color:'#34d399' }}>Welcome to {paymentSuccess === 'vip' ? 'VIP Rollers' : 'Premium'}!</div>
            <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.7)', marginTop:'4px' }}>Your subscription is now active. Enjoy full access to all picks!</div>
          </div>
        )}
        {(() => {
          const pageConfig = [
            { key:'home',      tierRequired: null, component: () => <HomePageView onAuthSuccess={handleAuthSuccess} isAuthenticated={isAuthenticated} authUser={authUser} accountSettingsRequest={accountSettingsRequest} /> },
            { key:'punchestown', tierRequired: null, component: () => <PunchestownTomorrowView /> },
            { key:'yesterday', tierRequired: 'premium', component: () => <YesterdayResultsView isFreeUser={!hasPaidEntitlement} /> },
            { key:'picks',    tierRequired: 'premium', component: () => <Top5PicksView /> },
            { key:'picks5',   tierRequired: 'premium', component: () => <Top5PicksView /> },
            { key:'laythe',   tierRequired: 'vip', component: () => <LayTheFavView /> },
            { key:'majors',   tierRequired: 'premium', component: () => <MajorRacesView /> },
            { key:'account',  tierRequired: 'premium', component: () => <MyAccountView authUser={authUser} onLogout={handleLogout} accountSettingsRequest={accountSettingsRequest} /> },
            { key:'admin',    tierRequired: 'admin', component: () => isAdmin ? <AdminView authUser={authUser} /> : null },
          ];
          const cfg = pageConfig.find(p => p.key === page);
          if (!cfg) return <HomePageView onAuthSuccess={handleAuthSuccess} isAuthenticated={isAuthenticated} authUser={authUser} accountSettingsRequest={accountSettingsRequest} />;

          // Guests can see all tabs but clicking protected ones shows sign-up prompt
          // (Removed auto-redirect to home - now handled in hasAccess check below)
          
          // Check if user has access
          let hasAccess = true;
          let requiredTier = cfg.tierRequired;
          if (requiredTier === 'admin') {
            hasAccess = isAdmin;
          } else if (requiredTier === 'vip') {
            hasAccess = hasVipEntitlement;
          } else if (requiredTier === 'premium') {
            hasAccess = hasPaidEntitlement;
          }
          
          // If no access, show gating message
          if (!hasAccess) {
            const vipMessage = requiredTier === 'vip';
            return (
              <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'16px', padding:'60px 32px', textAlign:'center', maxWidth:'640px', margin:'40px auto' }}>
                <div style={{ fontSize:'60px', marginBottom:'24px' }}>🔒</div>
                <h2 style={{ fontSize:'28px', fontWeight:'900', color:'white', marginBottom:'12px' }}>
                  {isAuthenticated
                    ? (vipMessage ? 'VIP Rollers Exclusive' : 'Premium Access Required')
                    : 'Unlock This Content'}
                </h2>
                <p style={{ fontSize:'16px', color:'rgba(255,255,255,0.7)', marginBottom:'28px', lineHeight:'1.6' }}>
                  {isAuthenticated ? (
                    vipMessage ?
                      'This content is exclusive to VIP Rollers members. Upgrade now to unlock premium features and VIP-only strategies.' :
                      'This page requires a Premium or VIP subscription. Subscribe today to unlock all picks and analysis.'
                  ) : (
                    <>
                      Get instant access to all premium picks, daily analysis, and our AI-powered value model.
                      <br/>
                      <strong style={{ color:'#34d399' }}>Start your 7-day free trial — no payment required!</strong>
                    </>
                  )}
                </p>
                <div style={{ display:'flex', flexDirection:'column', gap:'12px', alignItems:'center' }}>
                  <button onClick={() => {
                    trackEvent('signup_click', { location: 'gated_page_' + cfg.key, tier: isAuthenticated ? (vipMessage ? 'vip' : 'premium') : 'premium_trial', user_status: isAuthenticated ? 'authenticated' : 'guest' });
                    setPage('home');
                    setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 100);
                  }} style={{
                    background:'linear-gradient(135deg,#059669 0%,#047857 100%)',
                    border:'2px solid #10b981', borderRadius:'10px', padding:'16px 40px',
                    color:'white', fontSize:'18px', fontWeight:'800',
                    cursor:'pointer', transition:'all 0.2s',
                    boxShadow:'0 4px 12px rgba(5,150,105,0.3)',
                    minWidth:'240px'
                  }}>
                    {isAuthenticated
                      ? (vipMessage ? 'Upgrade to VIP' : 'View Plans')
                      : '🎁 Start Free 7-Day Trial'}
                  </button>
                  {!isAuthenticated && (
                    <button onClick={() => {
                      trackEvent('signin_click', { location: 'gated_page_' + cfg.key, user_status: 'guest' });
                      setPage('home');
                      setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 100);
                    }} style={{
                      background:'transparent',
                      border:'2px solid rgba(255,255,255,0.25)', borderRadius:'10px', padding:'12px 32px',
                      color:'rgba(255,255,255,0.7)', fontSize:'14px', fontWeight:'700',
                      cursor:'pointer', transition:'all 0.2s'
                    }}>
                      Already a member? Sign In
                    </button>
                  )}
                </div>
                <div style={{ marginTop:'24px', padding:'16px', background:'rgba(52,211,153,0.08)', border:'1px solid rgba(52,211,153,0.25)', borderRadius:'10px' }}>
                  <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.6)', lineHeight:'1.6' }}>
                    ✓ No credit card required for trial<br/>
                    ✓ Full Premium access for 7 days<br/>
                    ✓ Cancel anytime, no questions asked
                  </div>
                </div>
              </div>
            );
          }
          
          return cfg.component();
        })()}
      </main>
    </div>
  );
}

// ---- Analysis Pipeline Checklist ----
function AnalysisPipeline({ stages, signalCoverage, runTime, isMobile }) {
  if (!stages || stages.length === 0) return null;
  const allOk     = stages.every(s => s.ok);
  const failCount = stages.filter(s => !s.ok).length;
  const headerColor = allOk ? '#34d399' : '#fbbf24';
  const headerBg    = allOk ? 'rgba(5,150,105,0.12)' : 'rgba(245,158,11,0.12)';
  const borderColor = allOk ? 'rgba(52,211,153,0.35)' : 'rgba(251,191,36,0.4)';
  const runTimeStr  = runTime
    ? new Date(runTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    : null;
  return (
    <div style={{ background: headerBg, border: `1px solid ${borderColor}`, borderRadius: '10px', padding: '12px 16px', marginBottom: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: headerColor, fontWeight: '800' }}>
          {allOk ? '✓ Analysis complete — all signals active' : `⚠ ${failCount} analysis stage${failCount > 1 ? 's' : ''} incomplete`}
        </span>
        {runTimeStr && <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)' }}>Last run {runTimeStr}</span>}
      </div>
      {/* Stage pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: signalCoverage && Object.keys(signalCoverage).length > 0 ? '10px' : '0' }}>
        {stages.map(s => (
          <span key={s.id} title={s.detail} style={{
            background: s.ok ? 'rgba(5,150,105,0.2)' : 'rgba(234,179,8,0.15)',
            border: `1px solid ${s.ok ? 'rgba(52,211,153,0.4)' : 'rgba(251,191,36,0.5)'}`,
            borderRadius: '6px', padding: '3px 10px', fontSize: '11px', fontWeight: '700',
            color: s.ok ? '#34d399' : '#fbbf24', cursor: 'help', whiteSpace: 'nowrap',
          }}>
            {s.ok ? '✓' : '⚠'} {s.label}
          </span>
        ))}
      </div>
      {/* Signal coverage bars */}
      {signalCoverage && Object.keys(signalCoverage).length > 0 && (
        <div>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '6px' }}>
            Signal coverage (% of horses today where each factor fired)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: '5px' }}>
            {Object.entries(signalCoverage).map(([label, pct]) => (
              <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'rgba(255,255,255,0.55)' }}>
                  <span>{label}</span><span style={{ color: pct > 30 ? '#34d399' : pct > 0 ? '#fbbf24' : '#ef4444', fontWeight: '700' }}>{pct}%</span>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.1)', borderRadius: '2px', height: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', background: pct > 30 ? '#059669' : pct > 0 ? '#d97706' : '#ef4444', borderRadius: '2px' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Daily Picks ----
const SCORE_LABELS = {
  form:              'Recent Form',
  form_score:        'Recent Form',
  recent_win:        'Last Race Win',
  total_wins:        'Form Wins',
  consistency:       'Form Places',
  market_position:   'Market Position',
  market_leader:     'Market Leader Bonus',
  market_bonus:      'Market Bonus',
  optimal_odds:      'Odds Position',
  sweet_spot:        'Odds Sweet Spot',
  trainer:           'Trainer Quality',
  trainer_score:     'Trainer Quality',
  trainer_reputation:'Trainer Quality',
  jockey:            'Jockey Quality',
  jockey_score:      'Jockey Quality',
  jockey_quality:    'Jockey Quality',
  going:             'Going Suitability',
  going_score:       'Going Suitability',
  going_suitability: 'Going Suitability',
  class:             'Class Level',
  class_score:       'Class Level',
  distance_suitability: 'Distance Suitability',
  distance:          'Distance Suitability',
  distance_score:    'Distance Suitability',
  cd_bonus:          'Course+Distance Winner',
  headgear:          'Headgear Change',
  course:            'Course Form',
  course_score:      'Course Form',
  course_performance:'Course Performance',
  weight:            'Weight Advantage',
  weight_penalty:    'Weight Penalty',
  draw:              'Draw Advantage',
  age:               'Age Profile',
  age_bonus:         'Age Bonus',
  bounce_back:       'Bounce-Back Pattern',
  history_bonus:     'DB History Bonus',
  history:           'DB History Bonus',
  database_history:  'DB History Bonus',
  base:              'Base Score',
  odds_value:        'Odds Value',
  price_move:        'Price Move',
  favorite_correction:'Favourite Bonus',
  track_pattern_bonus:'Track Pattern',
  novice_penalty:    'Novice Race Penalty',
  aw_low_class_penalty:  'AW Low Class Penalty',
  unexposed_bonus:         'Unexposed/Improving',
  claiming_jockey:         'Claiming Jockey Allowance',
  heavy_going_penalty:     'Heavy Going Penalty',
  official_rating_bonus:   'Official Rating',
  deep_form:               'Deep Form Analysis',
  short_form_improvement:  'Recent Improvement',
  meeting_focus:           'Meeting Focus',
  jockey_course_bonus:     'Jockey Course Record',
  trainer_course_bonus:    'Trainer Course Record',
  market_steam:            'Market Steam/Drift',
  timeform_stars:          'Timeform Rating',
  cheltenham_festival:     'Cheltenham Festival',
};

function DailyPicksView({ isFreeUser, onUpgrade, authUser }) {
  const [allPicks, setAllPicks] = useState([]);
  const [serverTopCalls, setServerTopCalls] = useState(null);
  const [payloadStatus, setPayloadStatus] = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [cumulRoi, setCumulRoi] = useState(null);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);
  const [now, setNow]           = useState(new Date());
  const [upgradeLoading, setUpgradeLoading] = useState(null);
  const [upgradeError, setUpgradeError]     = useState(null);

  const doSubscribe = async (tier) => {
    if (!authUser?.email) return;
    setUpgradeLoading(tier); setUpgradeError(null);
    trackEvent('signup_click', {
      location: 'daily_picks_upgrade',
      tier,
      user_status: 'authenticated',
    });
    try {
      const res = await fetch(`${API_BASE_URL}/api/create-checkout-session`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email, tier })
      });
      const data = await res.json();
      if (data.url) {
        trackEvent('begin_checkout', {
          location: 'daily_picks_upgrade',
          tier,
          user_status: 'authenticated',
        });
        window.location.href = data.url;
      }
      else { setUpgradeError(data.error || 'Checkout failed'); setUpgradeLoading(null); }
    } catch (e) { setUpgradeError('Network error'); setUpgradeLoading(null); }
  };

  useEffect(() => { const t = setInterval(() => setNow(new Date()), 60000); return () => clearInterval(t); }, []);
  useEffect(() => { const h = () => setIsMobile(window.innerWidth < 768); window.addEventListener('resize', h); return () => window.removeEventListener('resize', h); }, []);
  useEffect(() => { loadPicks(); const iv = setInterval(() => { const h = new Date().getHours(); if (h >= 12 && h <= 18) loadPicks(); }, 30*60*1000); return () => clearInterval(iv); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadPicks = async () => {
    setLoading(true); setError(null);
    try {
      const [res, roiRes] = await Promise.all([
        fetch(API_BASE_URL + '/api/results/today'),
        fetch(API_BASE_URL + '/api/results/cumulative-roi'),
      ]);
      const data = await res.json();
      const roiData = await roiRes.json().catch(() => null);
      if (roiData?.success) setCumulRoi(roiData);
      if (data.success) {
        const picks = (data.picks || []).filter(p => p.show_in_ui !== false);
        // Sort by score descending so the same top 2 are deterministic all day
        picks.sort((a, b) => parseFloat(b.comprehensive_score || b.score || 0) - parseFloat(a.comprehensive_score || a.score || 0));
        setAllPicks(picks);
        setServerTopCalls(data.top_calls || null);
        setPayloadStatus(data.payload_status || null);
      } else setError(data.error || 'Failed to load picks');
    } catch (err) { setError('Network error: ' + err.message); }
    finally { setLoading(false); }
  };

  // Free tier: top 2 picks only, remove once race is over
  const MAX_FREE_PICKS = 2;
  const top2 = allPicks.slice(0, MAX_FREE_PICKS);
  const visiblePicks = top2.filter(pick => {
    if (!pick.race_time) return true;
    try {
      const rt = new Date(pick.race_time.endsWith('Z') || pick.race_time.includes('+') ? pick.race_time : pick.race_time + 'Z');
      return rt > now; // hide once race_time has passed
    } catch { return true; }
  });
  const hiddenCount = Math.max(0, allPicks.length - MAX_FREE_PICKS);

  const today = new Date().toLocaleDateString('en-GB', { weekday:'long', day:'numeric', month:'long', year:'numeric' });

  const tierInfo = score => {
    const s = parseFloat(score || 0);
    if (s >= 95) return { bg: '#d97706', label: 'ELITE' };
    if (s >= 90) return { bg: '#059669', label: 'STRONG' };
    if (s >= 80) return { bg: '#3b82f6', label: 'GOOD' };
    return { bg: '#0891b2', label: 'VALUE' };
  };

  const getScore = (pick) => parseFloat(pick?.comprehensive_score || pick?.score || 0);
  const getGap = (pick) => parseFloat(pick?.score_gap || 0);
  const getOdds = (pick) => {
    const raw = pick?.odds;
    if (raw == null || raw === '') return 0;
    if (typeof raw === 'number') return raw;
    const txt = String(raw).trim();
    if (txt.includes('/')) {
      const parts = txt.split('/');
      const num = parseFloat(parts[0]);
      const den = parseFloat(parts[1]);
      if (!Number.isNaN(num) && !Number.isNaN(den) && den > 0) return 1 + (num / den);
    }
    const dec = parseFloat(txt);
    return Number.isNaN(dec) ? 0 : dec;
  };

  const buildDailyTopCalls = (picks) => {
    if (!Array.isArray(picks) || picks.length === 0) {
      return { sureThing: null, nap: null, mustWin: null };
    }

    const ranked = [...picks].sort((a, b) => getScore(b) - getScore(a));
    const nap = ranked[0] || null;

    // Sure Thing: strongest high-confidence runner in a sensible odds band.
    const sureThingPool = ranked.filter((p) => {
      const s = getScore(p);
      const o = getOdds(p);
      return s >= 85 && (o === 0 || (o >= 1.6 && o <= 4.5));
    });
    const sureThing = (sureThingPool[0] || nap);

    // Must Win: best separation edge (score gap) with a minimum quality floor.
    const mustWinPool = ranked
      .filter((p) => getScore(p) >= 82)
      .sort((a, b) => getGap(b) - getGap(a) || getScore(b) - getScore(a));
    let mustWin = mustWinPool[0] || nap;

    // Keep labels varied where possible.
    if (mustWin && nap && mustWin.horse === nap.horse && ranked[1]) {
      mustWin = ranked[1];
    }

    return { sureThing, nap, mustWin };
  };

  const formatRaceTime = rt => {
    if (!rt) return { date: '', time: '' };
    try {
      const d = new Date(rt.endsWith('Z') || rt.includes('+') ? rt : rt + 'Z');
      const tz = { timeZone: 'Europe/Dublin' };
      return {
        date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', year:'numeric', ...tz }),
        time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12: false, ...tz }),
      };
    } catch { return { date: rt.substring(0,10), time: rt.substring(11,16) }; }
  };

  const localTopCalls = buildDailyTopCalls(allPicks);
  const topCalls = {
    sureThing: serverTopCalls?.sure_thing || localTopCalls.sureThing,
    nap: serverTopCalls?.nap || localTopCalls.nap,
    mustWin: serverTopCalls?.must_win || localTopCalls.mustWin,
  };

  const bettingWindow = (pick) => {
    if (!pick.race_time) return { label: 'Anytime Today', desc: 'Long price — odds stable', bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.4)', color: '#60a5fa' };
    try {
      const raceDate = new Date(pick.race_time.endsWith('Z') || pick.race_time.includes('+') ? pick.race_time : pick.race_time + 'Z');
      const minsToRace = (raceDate - now) / 60000;
      if (minsToRace < 0) return { label: 'Race Complete', desc: 'Check results', bg: 'rgba(107,114,128,0.12)', border: 'rgba(107,114,128,0.4)', color: '#9ca3af' };
      if (minsToRace < 15) return { label: '🔥 Bet Now', desc: 'Race imminent', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.5)', color: '#ef4444' };
      if (minsToRace < 120) return { label: '⏰ 1-2hrs Before', desc: 'Price stable until near off', bg: 'rgba(234,179,8,0.12)', border: 'rgba(234,179,8,0.4)', color: '#eab308' };
      return { label: '🏦 Anytime Today', desc: 'Long price — odds stable', bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.4)', color: '#60a5fa' };
    } catch { return { label: 'Anytime Today', desc: '', bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.4)', color: '#60a5fa' }; }
  };

  if (loading) return <div style={{ textAlign:'center', padding:'60px 20px', color:'white' }}><div style={{ fontSize:'18px', opacity:0.8 }}>Loading today's picks...</div></div>;
  if (error) return <div style={{ background:'rgba(239,68,68,0.15)', border:'1px solid #ef4444', borderRadius:'10px', padding:'24px', textAlign:'center', color:'white' }}><div style={{ fontWeight:'700', marginBottom:'6px' }}>Error loading picks</div><div style={{ fontSize:'13px', opacity:0.8, marginBottom:'16px' }}>{error}</div><button onClick={loadPicks} style={{ background:'#059669', border:'none', borderRadius:'6px', color:'white', padding:'8px 20px', cursor:'pointer', fontWeight:'700' }}>Retry</button></div>;

  // Don't reveal picks until 1pm Dublin time — selections may change as new info arrives
  const dublinHour = parseInt(now.toLocaleString('en-GB', { hour:'numeric', hour12:false, timeZone:'Europe/Dublin' }));
  if (dublinHour < 13) return (
    <div style={{ textAlign:'center', padding:'60px 20px' }}>
      <div style={{ fontSize:'48px', marginBottom:'16px' }}>🐎</div>
      <div style={{ fontSize:'20px', fontWeight:'800', color:'white', marginBottom:'8px' }}>Today's Picks</div>
      <div style={{ fontSize:'15px', color:'rgba(255,255,255,0.7)', lineHeight:'1.7' }}>Picks are finalised and published at <strong style={{ color:'#34d399' }}>1:00pm</strong> daily.</div>
      <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.45)', marginTop:'12px' }}>Our AI is analysing today's races, odds, going and form data.<br/>Check back after 1pm for your selections.</div>
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div style={{ background:'linear-gradient(135deg,#1e3a5f 0%,#047857 100%)', border:'2px solid #10b981', borderRadius:'14px', padding: isMobile ? '16px 14px' : '22px 28px', marginBottom:'20px', color:'white', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div style={{ fontSize: isMobile ? '20px' : '24px', fontWeight:'900' }}>{today}</div>
        </div>
        <button onClick={loadPicks} style={{ background:'rgba(255,255,255,0.15)', border:'1px solid rgba(255,255,255,0.4)', borderRadius:'8px', color:'white', padding:'8px 18px', cursor:'pointer', fontSize:'13px', fontWeight:'600' }}>Refresh</button>
      </div>

      {/* ROI */}
      {cumulRoi?.success && (() => {
        const rv = cumulRoi.roi ?? 0; const rs = cumulRoi.settled || 0;
        return (
          <div style={{ background: rv >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.13)', border: `1.5px solid ${rv >= 0 ? 'rgba(16,185,129,0.45)' : 'rgba(239,68,68,0.4)'}`, borderRadius:'14px', padding: isMobile ? '14px 16px' : '18px 24px', marginBottom:'20px', display:'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', justifyContent:'space-between', gap:'12px' }}>
            <div style={{ display:'flex', alignItems:'center', gap: isMobile ? '14px' : '20px' }}>
              <div style={{ fontSize: isMobile ? '28px' : '38px' }}>💰</div>
              <div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'1.2px', fontWeight:'700', marginBottom:'4px' }}>Return on Investment</div>
                <div style={{ fontSize: isMobile ? '26px' : '40px', fontWeight:'900', color: rv >= 0 ? '#34d399' : '#f87171', lineHeight:1 }}>{rv >= 0 ? '+' : ''}{rv.toFixed(1)}%</div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'4px' }}>Since 22 Mar · {rs} settled</div>
              </div>
            </div>
            <div style={{ textAlign: isMobile ? 'left' : 'right' }}>
              <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)', lineHeight:'1.6' }}>
                Across all bets, every €1 staked returned <span style={{ color: rv >= 0 ? '#34d399' : '#f87171', fontWeight:'700' }}>€{(1 + rv / 100).toFixed(2)}</span> on average — a {rv >= 0 ? 'profit' : 'loss'} of <span style={{ color: rv >= 0 ? '#34d399' : '#f87171', fontWeight:'700' }}>€{Math.abs(rv / 100).toFixed(2)}</span> per bet
              </div>
              <div style={{ marginTop:'8px' }}>
                <span onClick={() => { fetch(API_BASE_URL + '/api/results/export-csv').then(r => r.text()).then(csv => { const blob = new Blob([csv], { type: 'text/csv' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'BetBudAI_ROI_Data.csv'; a.click(); URL.revokeObjectURL(url); }).catch(() => {}); }}
                  style={{ cursor:'pointer', fontSize:'12px', fontWeight:'700', color:'white', background:'linear-gradient(135deg,#059669,#047857)', border:'none', borderRadius:'8px', padding:'8px 18px', display:'inline-flex', alignItems:'center', gap:'6px' }}>
                  📥 Download Full History CSV
                </span>
              </div>
            </div>
          </div>
        );
      })()}

      {(topCalls.sureThing || topCalls.nap || topCalls.mustWin) && (
        <div style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.14)', borderRadius:'12px', padding: isMobile ? '12px' : '14px', marginBottom:'16px' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'10px', flexWrap:'wrap', gap:'8px' }}>
            <div style={{ color:'white', fontSize:'15px', fontWeight:'800' }}>Top Picks</div>
            <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
              {payloadStatus && (
                <span style={{
                  fontSize:'10px',
                  fontWeight:'800',
                  color: payloadStatus.payload_complete ? '#34d399' : '#fbbf24',
                  background: payloadStatus.payload_complete ? 'rgba(16,185,129,0.18)' : 'rgba(245,158,11,0.18)',
                  border: payloadStatus.payload_complete ? '1px solid rgba(16,185,129,0.35)' : '1px solid rgba(245,158,11,0.35)',
                  borderRadius:'999px',
                  padding:'3px 8px',
                  letterSpacing:'0.4px'
                }}>
                  {payloadStatus.payload_complete ? 'PAYLOAD COMPLETE' : 'PAYLOAD PARTIAL'}
                </span>
              )}
              <div style={{ color:'rgba(255,255,255,0.6)', fontSize:'11px' }}>Daily AI calls</div>
            </div>
          </div>
          {payloadStatus && (
            <div style={{ color: payloadStatus.payload_complete ? '#a7f3d0' : '#fcd34d', fontSize:'10px', fontWeight:'600', marginBottom:'10px', display:'flex', alignItems:'center', gap:'5px' }}>
              {payloadStatus.payload_complete ? '✓' : '⏳'} {payloadStatus.payload_complete ? 'Full analysis complete' : 'Analysis in progress'} — {payloadStatus.payload_complete ? 'Field changes tracked & improver boost applied' : 'field changes and improver scoring pending'}
            </div>
          )}
          {payloadStatus && !payloadStatus.payload_complete && (
            <div style={{ color:'rgba(255,255,255,0.72)', fontSize:'11px', marginBottom:'8px' }}>
              {`Selection completeness: ${payloadStatus.picks_count || 0} picks, reason: ${payloadStatus.reason || 'incomplete'}`}
            </div>
          )}
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, minmax(0, 1fr))', gap:'10px' }}>
            {[
              { key: 'sureThing', label: 'Sure Thing Winner', pick: topCalls.sureThing, tone: '#22c55e' },
              { key: 'nap', label: 'Nap of the Day', pick: topCalls.nap, tone: '#3b82f6' },
              { key: 'mustWin', label: 'Must Win Horse', pick: topCalls.mustWin, tone: '#f59e0b' },
            ].map(({ key, label, pick, tone }) => (
              <div key={key} style={{ background:'rgba(255,255,255,0.05)', border:`1px solid ${tone}55`, borderRadius:'10px', padding:'10px' }}>
                <div style={{ fontSize:'10px', fontWeight:'800', color:tone, letterSpacing:'0.6px', textTransform:'uppercase', marginBottom:'6px' }}>{label}</div>
                <div style={{ color:'white', fontSize:'15px', fontWeight:'800', marginBottom:'4px' }}>{pick?.horse || 'n/a'}</div>
                <div style={{ color:'rgba(255,255,255,0.7)', fontSize:'12px' }}>
                  {[pick?.course, pick?.race_time ? formatRaceTime(pick.race_time).time : '', pick?.odds ? `@ ${toFractional(pick.odds)}` : '']
                    .filter(Boolean)
                    .join(' | ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Picks */}
      {visiblePicks.length === 0 ? (
        <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'12px', padding:'48px 24px', textAlign:'center', color:'rgba(255,255,255,0.7)' }}>
          <div style={{ fontSize:'18px', fontWeight:'700', color:'white', marginBottom:'8px' }}>{allPicks.length > 0 ? "Today's free picks have finished" : 'No picks yet today'}</div>
          <div style={{ fontSize:'14px' }}>{allPicks.length > 0 ? 'Upgrade to Top 4 Picks and Intraday for full daily coverage including results.' : 'Picks are published daily at 1pm. Check back then.'}</div>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>
          {visiblePicks.map((pick, idx) => {
            const tier = tierInfo(pick.comprehensive_score || pick.score);
            const rank = idx + 1;
            const rankColors = { 1:'#d97706', 2:'#6b7280' };
            const ft = formatRaceTime(pick.race_time);
            const bw = bettingWindow(pick);
            return (
              <div key={idx} style={{ background:'white', borderRadius:'12px', padding: isMobile ? '14px 12px' : '20px 22px', borderLeft:`5px solid ${rankColors[rank] || tier.bg}`, boxShadow:'0 2px 12px rgba(0,0,0,0.1)' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'8px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                    <div style={{ background: rankColors[rank] || tier.bg, color:'white', borderRadius:'8px', padding:'6px 10px', textAlign:'center', minWidth:'44px' }}>
                      <div style={{ fontSize:'18px', fontWeight:'900' }}>#{rank}</div>
                      <div style={{ fontSize:'9px', fontWeight:'700', opacity:0.85, textTransform:'uppercase', lineHeight:'1' }}>Pick</div>
                    </div>
                    <div>
                      <div style={{ fontSize: isMobile ? '17px' : '20px', fontWeight:'800', color:'#111' }}>{pick.horse || 'Unknown'}</div>
                      <div style={{ display:'flex', flexWrap:'wrap', gap:'6px', marginTop:'6px', alignItems:'center' }}>
                        {pick.course && <span style={{ background:'#1e3a5f', color:'white', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'700' }}>{pick.course}</span>}
                        {ft.date && <span style={{ background:'#f3f4f6', color:'#374151', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'600' }}>{ft.date}</span>}
                        {ft.time && <span style={{ background:'#ecfdf5', color:'#065f46', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'700', border:'1px solid #a7f3d0' }}>{ft.time}</span>}
                      </div>
                    </div>
                  </div>
                  <div style={{ display:'flex', gap:'8px', alignItems:'center' }}>
                    {pick.odds && (
                      <div style={{ textAlign:'center' }}>
                        <div style={{ background:'#1e3a5f', color:'white', padding:'5px 14px', borderRadius:'8px', fontWeight:'900', fontSize:'22px' }}>{toFractional(pick.odds)}</div>
                        <div style={{ fontSize:'10px', color:'#6b7280', marginTop:'2px', fontWeight:'600' }}>ODDS</div>
                      </div>
                    )}
                    {pick.odds && parseFloat(pick.odds) <= 1.7 && (
                      <span style={{ background:'#fef3c7', color:'#92400e', border:'1px solid #fbbf24', borderRadius:'6px', padding:'4px 8px', fontSize:'11px', fontWeight:'700' }}>⚠ Low Odds Value</span>
                    )}
                    <span style={{ background: tier.bg, color:'white', padding:'5px 12px', borderRadius:'8px', fontSize:'12px', fontWeight:'700' }}>{tier.label}</span>
                  </div>
                </div>
                {/* Betting window */}
                <div style={{ marginTop:'10px', display:'inline-flex', alignItems:'center', gap:'6px', background: bw.bg, border:`1px solid ${bw.border}`, borderRadius:'7px', padding:'5px 12px' }}>
                  <span style={{ fontSize:'13px', fontWeight:'800', color: bw.color }}>{bw.label}</span>
                  <span style={{ fontSize:'11px', color:'#6b7280' }}>— {bw.desc}</span>
                </div>
                {/* Trainer / Jockey / Form */}
                <div style={{ fontSize:'13px', color:'#374151', marginTop:'12px', display:'flex', gap:'18px', flexWrap:'wrap', alignItems:'center' }}>
                  {pick.trainer && <span><strong>Trainer:</strong> {pick.trainer}</span>}
                  {pick.jockey && <span><strong>Jockey:</strong> {pick.jockey}</span>}
                  {pick.form && <span style={{ background:'#f3f4f6', borderRadius:'5px', padding:'2px 8px', fontFamily:'monospace', fontWeight:'700', color:'#1e3a5f', letterSpacing:'1px' }}>Form: {pick.form}</span>}
                  {renderScoreGapBadge(pick.score_gap)}
                </div>
                {/* Score badge */}
                {(() => {
                  const score = parseFloat(pick.comprehensive_score || pick.score || 0);
                  if (!score) return null;
                  return (
                    <div style={{ marginTop:'10px', padding:'10px 14px', background:`${tier.bg}18`, borderRadius:'8px', borderLeft:`3px solid ${tier.bg}` }}>
                      <span style={{ background: tier.bg, color:'white', borderRadius:'5px', padding:'2px 9px', fontSize:'11px', fontWeight:'800' }}>{tier.label}</span>
                      <span style={{ fontSize:'12px', fontWeight:'700', color:'#1e3a5f', marginLeft:'8px' }}>Score: {score.toFixed(0)}</span>
                    </div>
                  );
                })()}
              </div>
            );
          })}
          {/* Upgrade banner — two tiers */}
          {hiddenCount > 0 && (
              <div style={{ marginTop:'8px' }}>
                <div style={{ textAlign:'center', marginBottom:'14px' }}>
                  <div style={{ fontSize:'20px', marginBottom:'6px' }}>🔒</div>
                  <div style={{ fontSize:'16px', fontWeight:'800', color:'white', marginBottom:'4px' }}>+{hiddenCount} more pick{hiddenCount > 1 ? 's' : ''} available</div>
                  <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)' }}>Unlock everything with Premium or VIP</div>
                </div>
                {upgradeError && <div style={{ background:'rgba(239,68,68,0.15)', border:'1px solid rgba(239,68,68,0.4)', borderRadius:'8px', padding:'8px', textAlign:'center', marginBottom:'10px', color:'#f87171', fontSize:'12px' }}>{upgradeError}</div>}
                <div style={{ display:'flex', gap:'10px', flexWrap:'wrap', justifyContent:'center' }}>
                  {/* PREMIUM */}
                  <div style={{ flex:'1 1 160px', maxWidth:'260px', background:'linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.1))', border:'2px solid rgba(99,102,241,0.5)', borderRadius:'14px', padding:'18px 16px', position:'relative' }}>
                    <div style={{ position:'absolute', top:'-10px', left:'50%', transform:'translateX(-50%)', background:'linear-gradient(135deg,#6366f1,#7c3aed)', borderRadius:'12px', padding:'2px 12px', fontSize:'9px', fontWeight:'800', color:'white', textTransform:'uppercase', letterSpacing:'0.5px', whiteSpace:'nowrap' }}>Most Popular</div>
                    <div style={{ fontSize:'12px', fontWeight:'700', textTransform:'uppercase', letterSpacing:'1px', color:'#818cf8', marginBottom:'4px', textAlign:'center' }}>Premium</div>
                    <div style={{ textAlign:'center', marginBottom:'10px' }}><span style={{ fontSize:'26px', fontWeight:'900', color:'white' }}>€9.99</span><span style={{ fontSize:'12px', color:'rgba(255,255,255,0.4)' }}>/mo</span></div>
                    <ul style={{ listStyle:'none', padding:0, margin:'0 0 14px', fontSize:'12px', color:'rgba(255,255,255,0.7)', lineHeight:'1.9' }}>
                      <li>✓ 4+ tips daily</li>
                      <li>✓ 2 watchlist selections daily</li>
                      <li>✓ Daily featured meeting</li>
                      <li>✓ All results &amp; live ROI tracking</li>
                      <li>✓ Priority support</li>
                    </ul>
                    <button onClick={() => doSubscribe('premium')} disabled={!!upgradeLoading}
                      style={{ width:'100%', background:'linear-gradient(135deg,#6366f1,#7c3aed)', border:'none', borderRadius:'8px', padding:'10px', color:'white', fontSize:'13px', fontWeight:'800', cursor:upgradeLoading?'wait':'pointer', opacity:upgradeLoading==='vip'?0.5:1 }}>
                      {upgradeLoading==='premium' ? 'Redirecting...' : 'Get Premium'}
                    </button>
                  </div>
                  {/* VIP ROLLERS */}
                  <div style={{ flex:'1 1 160px', maxWidth:'260px', background:'linear-gradient(135deg,rgba(245,158,11,0.12),rgba(251,191,36,0.06))', border:'2px solid rgba(245,158,11,0.45)', borderRadius:'14px', padding:'18px 16px', position:'relative' }}>
                    <div style={{ position:'absolute', top:'-10px', left:'50%', transform:'translateX(-50%)', background:'linear-gradient(135deg,#f59e0b,#d97706)', borderRadius:'12px', padding:'2px 12px', fontSize:'9px', fontWeight:'800', color:'white', textTransform:'uppercase', letterSpacing:'0.5px', whiteSpace:'nowrap' }}>Best Value</div>
                    <div style={{ fontSize:'12px', fontWeight:'700', textTransform:'uppercase', letterSpacing:'1px', color:'#fbbf24', marginBottom:'4px', textAlign:'center' }}>👑 VIP Rollers</div>
                    <div style={{ textAlign:'center', marginBottom:'10px' }}><span style={{ fontSize:'26px', fontWeight:'900', color:'white' }}>€49.99</span><span style={{ fontSize:'12px', color:'rgba(255,255,255,0.4)' }}>/mo</span></div>
                    <ul style={{ listStyle:'none', padding:0, margin:'0 0 14px', fontSize:'12px', color:'rgba(255,255,255,0.7)', lineHeight:'1.9' }}>
                      <li>✓ 4+ tips daily + 2 watchlist picks</li>
                      <li>✓ Early ante-post selections</li>
                      <li>✓ Lay the vulnerable favourite</li>
                      <li>✓ Major race previews</li>
                      <li>✓ Priority support</li>
                      <li style={{fontSize:'10px',color:'rgba(255,255,255,0.45)',marginTop:'4px'}}>⚡ Exchange account required for maximum benefit</li>
                    </ul>
                    <button onClick={() => doSubscribe('vip')} disabled={!!upgradeLoading}
                      style={{ width:'100%', background:'linear-gradient(135deg,#f59e0b,#d97706)', border:'none', borderRadius:'8px', padding:'10px', color:'white', fontSize:'13px', fontWeight:'800', cursor:upgradeLoading?'wait':'pointer', opacity:upgradeLoading==='premium'?0.5:1 }}>
                      {upgradeLoading==='vip' ? 'Redirecting...' : 'Get VIP Rollers'}
                    </button>
                  </div>
                </div>
                <div style={{ textAlign:'center', fontSize:'10px', color:'rgba(255,255,255,0.3)', marginTop:'10px' }}>Powered by Stripe · Cancel anytime</div>
              </div>
          )}
        </div>
      )}

      <div style={{ marginTop:'28px', padding:'16px 20px', background:'rgba(255,255,255,0.07)', borderRadius:'10px', color:'rgba(255,255,255,0.6)', fontSize:'12px', textAlign:'center', lineHeight:'1.6' }}>
        Picks generated by AI analysis of Betfair odds, form, trainer &amp; jockey stats, going suitability and market movement.<br/>
        Model self-learns daily from race results · Always bet responsibly.
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// UPGRADE CARDS (compact inline cards with subscribe buttons)
// ════════════════════════════════════════════════════════════════════════════
function UpgradeCards({ authUser }) {
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState(null);
  const [subStatus, setSubStatus] = useState(null);

  useEffect(() => {
    if (!authUser?.email) return;
    fetch(`${API_BASE_URL}/api/subscription-status`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: authUser.email })
    }).then(r => r.json()).then(data => setSubStatus(data)).catch(() => {});
  }, [authUser?.email]);

  const handleSubscribe = async (tier) => {
    setLoading(tier); setError(null);
    trackEvent('signup_click', {
      location: 'upgrade_cards',
      tier,
      user_status: authUser?.email ? 'authenticated' : 'guest',
    });
    try {
      const res = await fetch(`${API_BASE_URL}/api/create-checkout-session`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email, tier })
      });
      const data = await res.json();
      if (data.url) {
        trackEvent('begin_checkout', {
          location: 'upgrade_cards',
          tier,
          user_status: authUser?.email ? 'authenticated' : 'guest',
        });
        window.location.href = data.url;
      }
      else { setError(data.error || 'Failed to start checkout'); setLoading(null); }
    } catch (e) { setError('Network error. Please try again.'); setLoading(null); }
  };

  const currentTier = subStatus?.subscription_tier || authUser?.subscription_tier || 'free';
  const isActive = subStatus?.subscription_status === 'active' || subStatus?.subscription_status === 'canceling';
  const showTrialCta = currentTier === 'free' && !isActive;

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '16px' }}>
        <span style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>⚡ Upgrade Your Plan</span>
      </div>
      {error && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '10px', textAlign: 'center', marginBottom: '12px', color: '#f87171', fontSize: '13px' }}>{error}</div>
      )}
      <div style={{ display: 'flex', gap: '12px', maxWidth: '700px', margin: '0 auto', flexWrap: 'wrap', justifyContent: 'center' }}>
        {/* Free */}
        <div style={{ flex: '1 1 200px', maxWidth: '220px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '16px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#60a5fa', marginBottom: '4px' }}>7-Day Free Trial</div>
          <div style={{ fontSize: '24px', fontWeight: '900', color: 'white', marginBottom: '8px' }}>€0<span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>/mo</span></div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', lineHeight: '1.7', marginBottom: '10px' }}>No card details required · cancel anytime</div>
          {currentTier === 'free' ? (
            <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '8px', fontSize: '12px', fontWeight: '700', color: 'rgba(255,255,255,0.4)' }}>Current Plan</div>
          ) : <div style={{ height: '32px' }} />}
        </div>
        {/* Premium */}
        <div style={{ flex: '1 1 200px', maxWidth: '220px', background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1))', border: '2px solid rgba(99,102,241,0.5)', borderRadius: '12px', padding: '16px', textAlign: 'center', position: 'relative', boxShadow: '0 0 25px rgba(99,102,241,0.15)' }}>
          <div style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', borderRadius: '12px', padding: '2px 12px', fontSize: '9px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '0.5px' }}>⭐ Popular</div>
          <div style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#818cf8', marginBottom: '4px' }}>Premium</div>
          <div style={{ fontSize: '24px', fontWeight: '900', color: 'white', marginBottom: '8px' }}>€9.99<span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>/mo</span></div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', lineHeight: '1.65', marginBottom: '10px', textAlign: 'left' }}>
            ✓ 4+ Tips Daily<br/>
            ✓ 2 Watchlist Selections Daily<br/>
            ✓ Daily Featured Meeting<br/>
            ✓ All Results + Live ROI Tracking
          </div>
          {currentTier === 'premium' && isActive ? (
            <div style={{ background: 'rgba(52,211,153,0.15)', borderRadius: '8px', padding: '8px', fontSize: '12px', fontWeight: '700', color: '#34d399' }}>✓ Current Plan</div>
          ) : (
            <button onClick={() => handleSubscribe('premium')} disabled={!!loading}
              style={{ width: '100%', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', border: 'none', borderRadius: '8px', padding: '9px', color: 'white', fontSize: '13px', fontWeight: '800', cursor: loading ? 'wait' : 'pointer', opacity: loading === 'vip' ? 0.5 : 1 }}>
              {loading === 'premium' ? 'Redirecting...' : (showTrialCta ? 'Start 7-Day Free Trial' : 'Subscribe — €9.99/mo')}
            </button>
          )}
        </div>
        {/* VIP Rollers */}
        <div style={{ flex: '1 1 200px', maxWidth: '220px', background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(251,191,36,0.06))', border: '2px solid rgba(245,158,11,0.45)', borderRadius: '12px', padding: '16px', textAlign: 'center', position: 'relative', boxShadow: '0 0 25px rgba(245,158,11,0.1)' }}>
          <div style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', background: 'linear-gradient(135deg, #f59e0b, #d97706)', borderRadius: '12px', padding: '2px 12px', fontSize: '9px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '0.5px' }}>🔥 Best Value</div>
          <div style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#fbbf24', marginBottom: '4px' }}>👑 VIP Rollers</div>
          <div style={{ fontSize: '24px', fontWeight: '900', color: 'white', marginBottom: '8px' }}>€49.99<span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>/mo</span></div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', lineHeight: '1.65', marginBottom: '4px', textAlign: 'left' }}>
            ✓ Everything in Premium<br/>
            ✓ Early Ante-Post Major Race Selections<br/>
            ✓ Lay the Vulnerable Favourite<br/>
            ✓ Major Race Previews
          </div>
          <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.4)', marginBottom: '10px' }}>⚡ Exchange account required for max benefit</div>
          {currentTier === 'vip' && isActive ? (
            <div style={{ background: 'rgba(52,211,153,0.15)', borderRadius: '8px', padding: '8px', fontSize: '12px', fontWeight: '700', color: '#34d399' }}>✓ Current Plan</div>
          ) : (
            <button onClick={() => handleSubscribe('vip')} disabled={!!loading}
              style={{ width: '100%', background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: '8px', padding: '9px', color: 'white', fontSize: '13px', fontWeight: '800', cursor: loading ? 'wait' : 'pointer', opacity: loading === 'premium' ? 0.5 : 1 }}>
              {loading === 'vip' ? 'Redirecting...' : (showTrialCta ? 'Start 7-Day Free Trial' : 'Subscribe — €49.99/mo')}
            </button>
          )}
        </div>
      </div>
      <div style={{ textAlign: 'center', fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginTop: '10px' }}>Powered by Stripe · Cancel anytime</div>
      <RevolutPayOption authUser={authUser} compact />
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// REVOLUT / BANK TRANSFER PAYMENT OPTION
// ════════════════════════════════════════════════════════════════════════════
function RevolutPayOption({ authUser, compact }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(null);
  const IBAN = 'IE28REVO99036089671785';
  const IBAN_DISPLAY = 'IE28 REVO 9903 6089 6717 85';
  const BIC = 'REVOIE23';
  const REF = authUser?.username || authUser?.email || 'your-username';

  const copyText = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), 2000);
    }).catch(() => {});
  };

  if (compact && !expanded) {
    return (
      <div style={{ textAlign: 'center', marginTop: '10px' }}>
        <span onClick={() => setExpanded(true)} style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', textDecoration: 'underline', textDecorationStyle: 'dotted' }}>
          💶 Or pay via Revolut / Bank Transfer
        </span>
      </div>
    );
  }

  return (
    <div style={{ marginTop: compact ? '12px' : '28px', maxWidth: '520px', marginLeft: 'auto', marginRight: 'auto' }}>
      {!compact && (
        <div style={{ textAlign: 'center', marginBottom: '14px' }}>
          <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
            <span style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
            <span>or pay via Revolut / Bank Transfer</span>
            <span style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
          </div>
        </div>
      )}
      <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: compact ? '14px 16px' : '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <span style={{ fontSize: compact ? '14px' : '16px', fontWeight: '800', color: 'white' }}>💶 Bank Transfer</span>
          <span style={{ fontSize: '10px', background: 'rgba(52,211,153,0.15)', color: '#34d399', borderRadius: '6px', padding: '2px 8px', fontWeight: '700' }}>No fees</span>
        </div>
        <div style={{ display: 'grid', gap: '8px', fontSize: compact ? '12px' : '13px' }}>
          {/* IBAN */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '8px 12px' }}>
            <div>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>IBAN</div>
              <div style={{ color: 'white', fontWeight: '700', fontFamily: 'monospace', fontSize: compact ? '12px' : '14px' }}>{IBAN_DISPLAY}</div>
            </div>
            <span onClick={() => copyText(IBAN, 'iban')} style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: '6px', background: copied === 'iban' ? 'rgba(52,211,153,0.2)' : 'rgba(255,255,255,0.08)', color: copied === 'iban' ? '#34d399' : 'rgba(255,255,255,0.5)', fontSize: '11px', fontWeight: '600', transition: 'all 0.2s' }}>
              {copied === 'iban' ? '✓ Copied' : 'Copy'}
            </span>
          </div>
          {/* BIC */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '8px 12px' }}>
            <div>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>BIC / SWIFT</div>
              <div style={{ color: 'white', fontWeight: '700', fontFamily: 'monospace' }}>{BIC}</div>
            </div>
            <span onClick={() => copyText(BIC, 'bic')} style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: '6px', background: copied === 'bic' ? 'rgba(52,211,153,0.2)' : 'rgba(255,255,255,0.08)', color: copied === 'bic' ? '#34d399' : 'rgba(255,255,255,0.5)', fontSize: '11px', fontWeight: '600', transition: 'all 0.2s' }}>
              {copied === 'bic' ? '✓ Copied' : 'Copy'}
            </span>
          </div>
          {/* Beneficiary */}
          <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '8px 12px' }}>
            <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Beneficiary</div>
            <div style={{ color: 'white', fontWeight: '700' }}>BetBudAI</div>
          </div>
          {/* Reference */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05))', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px', padding: '8px 12px' }}>
            <div>
              <div style={{ color: '#818cf8', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Reference (important!)</div>
              <div style={{ color: 'white', fontWeight: '700', fontFamily: 'monospace' }}>{REF}</div>
            </div>
            <span onClick={() => copyText(REF, 'ref')} style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: '6px', background: copied === 'ref' ? 'rgba(52,211,153,0.2)' : 'rgba(255,255,255,0.08)', color: copied === 'ref' ? '#34d399' : 'rgba(255,255,255,0.5)', fontSize: '11px', fontWeight: '600', transition: 'all 0.2s' }}>
              {copied === 'ref' ? '✓ Copied' : 'Copy'}
            </span>
          </div>
        </div>
        <div style={{ marginTop: '10px', fontSize: '11px', color: 'rgba(255,255,255,0.4)', lineHeight: '1.6' }}>
          ⚡ Revolut-to-Revolut transfers are instant · Include your <strong style={{ color: 'rgba(255,255,255,0.6)' }}>username as reference</strong> so we can activate your account · €9.99/mo Premium · €49.99/mo VIP
        </div>
      </div>
      <LegalDisclaimerCard />
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// PRICING / SUBSCRIPTION VIEW
// ════════════════════════════════════════════════════════════════════════════
function PricingView({ authUser, onSuccess }) {
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState(null);
  const [subStatus, setSubStatus] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    trackEvent('view_pricing', {
      source: 'pricing_component',
      user_status: authUser?.email ? 'authenticated' : 'guest',
    });
  }, [authUser?.email]);

  // Fetch current subscription status
  useEffect(() => {
    if (!authUser?.email) return;
    fetch(`${API_BASE_URL}/api/subscription-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: authUser.email })
    })
      .then(r => r.json())
      .then(data => setSubStatus(data))
      .catch(() => {});
  }, [authUser?.email]);

  const handleSubscribe = async (tier) => {
    setLoading(tier); setError(null);
    trackEvent('signup_click', {
      location: 'pricing_view',
      tier,
      user_status: authUser?.email ? 'authenticated' : 'guest',
    });
    try {
      const res = await fetch(`${API_BASE_URL}/api/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email, tier })
      });
      const data = await res.json();
      if (data.url) {
        trackEvent('begin_checkout', {
          location: 'pricing_view',
          tier,
          user_status: authUser?.email ? 'authenticated' : 'guest',
        });
        window.location.href = data.url;
      }
      else { setError(data.error || 'Failed to start checkout'); setLoading(null); }
    } catch (e) { setError('Network error. Please try again.'); setLoading(null); }
  };

  const handleManageSubscription = async () => {
    setPortalLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/customer-portal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email })
      });
      const data = await res.json();
      if (data.url) { window.location.href = data.url; }
    } catch (e) { setError('Failed to open subscription management'); }
    setPortalLoading(false);
  };

  const currentTier = subStatus?.subscription_tier || authUser?.subscription_tier || 'free';
  const isActive = subStatus?.subscription_status === 'active' || subStatus?.subscription_status === 'canceling';

  return (
    <div style={{ padding: '20px 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: '900', color: 'white', marginBottom: '8px' }}>
          Upgrade Your Plan
        </h2>
        <p style={{ fontSize: '15px', color: 'rgba(255,255,255,0.6)', maxWidth: '500px', margin: '0 auto' }}>
          Get full access to AI-powered racing picks and unlock your edge
        </p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', textAlign: 'center', marginBottom: '16px', color: '#f87171', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {/* Current plan banner */}
      {isActive && currentTier !== 'free' && (
        <div style={{ background: 'rgba(52,211,153,0.12)', border: '1px solid rgba(52,211,153,0.35)', borderRadius: '10px', padding: '14px 18px', textAlign: 'center', marginBottom: '24px' }}>
          <span style={{ color: '#34d399', fontWeight: '700', fontSize: '14px' }}>
            ✓ You're on the {currentTier === 'vip' ? 'VIP Rollers' : 'Premium'} plan
          </span>
          {subStatus?.subscription_status === 'canceling' && (
            <span style={{ color: '#fbbf24', fontSize: '13px', marginLeft: '12px' }}>(cancels at period end)</span>
          )}
          <div style={{ marginTop: '10px' }}>
            <button onClick={handleManageSubscription} disabled={portalLoading}
              style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', padding: '8px 20px', color: 'white', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
              {portalLoading ? 'Opening...' : 'Manage Subscription'}
            </button>
          </div>
        </div>
      )}

      {/* Account status badges */}
      {subStatus && (
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: subStatus.has_card ? 'rgba(52,211,153,0.12)' : 'rgba(239,68,68,0.1)', border: `1px solid ${subStatus.has_card ? 'rgba(52,211,153,0.3)' : 'rgba(239,68,68,0.25)'}`, borderRadius: '8px', padding: '8px 16px' }}>
            <span style={{ fontSize: '16px' }}>{subStatus.has_card ? '💳' : '🚫'}</span>
            <div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Credit Card</div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: subStatus.has_card ? '#34d399' : '#f87171' }}>{subStatus.has_card ? 'Added' : 'Not Added'}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: subStatus.has_subscription ? 'rgba(52,211,153,0.12)' : 'rgba(255,255,255,0.05)', border: `1px solid ${subStatus.has_subscription ? 'rgba(52,211,153,0.3)' : 'rgba(255,255,255,0.12)'}`, borderRadius: '8px', padding: '8px 16px' }}>
            <span style={{ fontSize: '16px' }}>{subStatus.has_subscription ? '✅' : '⭕'}</span>
            <div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Paid Subscriber</div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: subStatus.has_subscription ? '#34d399' : 'rgba(255,255,255,0.5)' }}>{subStatus.has_subscription ? 'Yes' : 'No'}</div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', maxWidth: '700px', margin: '0 auto', padding: '0 8px' }}>

        {/* FREE TRIAL / FREE TIER */}
        <div style={{ background: 'linear-gradient(135deg, rgba(52,211,153,0.1), rgba(16,185,129,0.05))', border: '1px solid rgba(52,211,153,0.25)', borderRadius: '16px', padding: '28px 24px', position: 'relative' }}>
          <div style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#34d399', fontWeight: '700', marginBottom: '8px' }}>7-Day Free Trial</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '16px' }}>
            <span style={{ fontSize: '36px', fontWeight: '900', color: 'white' }}>€0</span>
            <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>for 7 days</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 20px', fontSize: '14px', color: 'rgba(255,255,255,0.7)', lineHeight: '2' }}>
            <li>✓ Full Premium access</li>
            <li>✓ 4+ tips daily + 2 watchlist picks</li>
            <li>✓ Daily featured meeting, results &amp; live ROI</li>
            <li>✓ No card details required</li>
            <li style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>Then €9.99/mo after trial</li>
          </ul>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '10px', padding: '10px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontWeight: '700', fontSize: '14px' }}>
            {currentTier === 'free' ? 'Current Plan' : '—'}
          </div>
        </div>

        {/* PREMIUM TIER */}
        <div style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08))', border: '2px solid rgba(99,102,241,0.4)', borderRadius: '16px', padding: '28px 24px', position: 'relative' }}>
          <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', borderRadius: '20px', padding: '4px 16px', fontSize: '11px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '1px' }}>Most Popular</div>
          <div style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#818cf8', fontWeight: '700', marginBottom: '8px' }}>Premium</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '16px' }}>
            <span style={{ fontSize: '36px', fontWeight: '900', color: 'white' }}>€9.99</span>
            <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>/month</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 20px', fontSize: '14px', color: 'rgba(255,255,255,0.7)', lineHeight: '2' }}>
            <li>✓ 4+ Tips Daily</li>
            <li>✓ 2 Watchlist Selections Daily</li>
            <li>✓ Daily Featured Meeting</li>
            <li>✓ All Results</li>
            <li>✓ Live ROI Tracking</li>
            <li>✓ Priority Support</li>
            <li>✓ Cancel Anytime</li>
          </ul>
          {currentTier === 'premium' && isActive ? (
            <div style={{ background: 'rgba(52,211,153,0.15)', borderRadius: '10px', padding: '10px', textAlign: 'center', color: '#34d399', fontWeight: '700', fontSize: '14px' }}>
              ✓ Current Plan
            </div>
          ) : (
            <button onClick={() => handleSubscribe('premium')} disabled={!!loading}
              style={{ width: '100%', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', border: 'none', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '15px', fontWeight: '800', cursor: loading ? 'wait' : 'pointer', opacity: loading === 'vip' ? 0.5 : 1 }}>
              {loading === 'premium' ? 'Redirecting to checkout...' : 'Subscribe to Premium'}
            </button>
          )}
        </div>

        {/* VIP TIER */}
        <div style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.1), rgba(251,191,36,0.06))', border: '2px solid rgba(245,158,11,0.35)', borderRadius: '16px', padding: '28px 24px', position: 'relative' }}>
          <div style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#fbbf24', fontWeight: '700', marginBottom: '8px' }}>VIP Rollers</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '16px' }}>
            <span style={{ fontSize: '36px', fontWeight: '900', color: 'white' }}>€49.99</span>
            <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>/month</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 20px', fontSize: '14px', color: 'rgba(255,255,255,0.7)', lineHeight: '2' }}>
            <li>✓ 4+ Tips Daily</li>
            <li>✓ 2 Watchlist Selections Daily</li>
            <li>✓ Daily Featured Meeting</li>
            <li>✓ All Results</li>
            <li>✓ Early Ante-Post Major Race Selections</li>
            <li>✓ Lay the Vulnerable Favourite</li>
            <li>✓ Live ROI Tracking</li>
            <li>✓ Major Race Previews</li>
            <li>✓ Priority support</li>
            <li>✓ Cancel anytime</li>
            <li style={{ color: 'rgba(255,255,255,0.45)' }}>⚡ Exchange account required for max benefit</li>
          </ul>
          {currentTier === 'vip' && isActive ? (
            <div style={{ background: 'rgba(52,211,153,0.15)', borderRadius: '10px', padding: '10px', textAlign: 'center', color: '#34d399', fontWeight: '700', fontSize: '14px' }}>
              ✓ Current Plan
            </div>
          ) : (
            <button onClick={() => handleSubscribe('vip')} disabled={!!loading}
              style={{ width: '100%', background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '15px', fontWeight: '800', cursor: loading ? 'wait' : 'pointer', opacity: loading === 'premium' ? 0.5 : 1 }}>
              {loading === 'vip' ? 'Redirecting to checkout...' : 'Subscribe to VIP Rollers'}
            </button>
          )}
        </div>
      </div>

      <div style={{ marginTop: '32px', textAlign: 'center', fontSize: '12px', color: 'rgba(255,255,255,0.4)', lineHeight: '1.8' }}>
        Payments securely processed by Stripe · Cancel anytime<br/>
        Subscriptions renew monthly · All prices in EUR
      </div>

      <RevolutPayOption authUser={authUser} compact />
      <LegalDisclaimerCard style={{ maxWidth: '600px', margin: '24px auto 0' }} />
    </div>
  );
}

// ---- MY ACCOUNT / PROFILE VIEW ----
function MyAccountView({ authUser, onLogout, accountSettingsRequest }) {
  const [subStatus, setSubStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancelDone, setCancelDone] = useState(false);
  const [emailPrefLoading, setEmailPrefLoading] = useState(false);
  const [emailPrefMessage, setEmailPrefMessage] = useState('');
  const [closeLoading, setCloseLoading] = useState(false);
  const [closeDone, setCloseDone] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!authUser?.email) return;
    fetch(`${API_BASE_URL}/api/subscription-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: authUser.email })
    })
      .then(r => r.json())
      .then(data => { setSubStatus(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [authUser?.email]);

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription? You\u2019ll keep access until the end of your current billing period.')) return;
    setCancelLoading(true); setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/cancel-subscription`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email })
      });
      const data = await res.json();
      if (data.success) {
        setCancelDone(true);
        setSubStatus(prev => ({ ...prev, subscription_status: 'canceling' }));
      } else { setError(data.error || 'Failed to cancel'); }
    } catch (e) { setError('Network error. Please try again.'); }
    setCancelLoading(false);
  };

  const handleDailyEmailPreference = async (optOut) => {
    setEmailPrefLoading(true);
    setError(null);
    setEmailPrefMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/daily-email-preference`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email, opt_out: optOut })
      });
      const data = await res.json();
      if (data.success) {
        setSubStatus(prev => ({ ...prev, daily_picks_email_opt_out: optOut }));
        setEmailPrefMessage(optOut ? 'Daily picks-ready emails are now turned off.' : 'Daily picks-ready emails are turned back on.');
      } else {
        setError(data.error || 'Failed to update daily email preference');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    }
    setEmailPrefLoading(false);
  };

  const handleCloseAccount = async () => {
    if (!window.confirm('Close this account permanently? This will disable sign-in and stop daily emails.')) return;
    setCloseLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/close-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authUser.email })
      });
      const data = await res.json();
      if (data.success) {
        setCloseDone(true);
        setTimeout(() => onLogout(), 1200);
      } else {
        setError(data.error || 'Failed to close account');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    }
    setCloseLoading(false);
  };

  const tierLabel = (t) => t === 'vip' ? 'VIP Rollers' : t === 'premium' ? 'Premium' : 'Free Trial';
  const tierColor = (t) => t === 'vip' ? '#fbbf24' : t === 'premium' ? '#818cf8' : '#34d399';
  const periodEnd = subStatus?.subscription_current_period_end
    ? new Date(subStatus.subscription_current_period_end * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : null;

  const cardStyle = { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' };
  const labelStyle = { fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px' };
  const valueStyle = { fontSize: '15px', fontWeight: '700', color: 'white' };

  if (loading) return <div style={{ textAlign: 'center', padding: '60px 24px', color: 'rgba(255,255,255,0.5)' }}>⏳ Loading your account...</div>;

  const tier = subStatus?.subscription_tier || 'free';
  const status = subStatus?.subscription_status || '';
  const isActive = status === 'active' || status === 'trialing';
  const isCanceling = status === 'canceling';
  const monthlyPrice = tier === 'vip' ? '€49.99' : '€9.99';
  const checkoutPending = subStatus?.checkout_pending;
  const emailOptedOut = !!subStatus?.daily_picks_email_opt_out;
  const canCloseAccount = !subStatus?.has_subscription && !isActive && !isCanceling;

  // If checkout is pending, show a prominent "Complete Setup" screen
  if (checkoutPending) {
    const handleCompleteSetup = async () => {
      setError(null);
      setCancelLoading(true);
      trackEvent('signup_click', {
        location: 'complete_setup',
        tier: 'premium_trial',
        user_status: authUser?.email ? 'authenticated' : 'guest',
      });
      try {
        const res = await fetch(`${API_BASE_URL}/api/create-checkout-session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authUser.email, tier: 'premium' })
        });
        const data = await res.json();
        if (data.url) {
          trackEvent('begin_checkout', {
            location: 'complete_setup',
            tier: 'premium_trial',
            user_status: authUser?.email ? 'authenticated' : 'guest',
          });
          window.location.href = data.url;
        }
        else { setError(data.error || 'Failed to start checkout'); }
      } catch (e) { setError('Network error. Please try again.'); }
      setCancelLoading(false);
    };

    return (
      <div style={{ padding: '20px 0', maxWidth: '500px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '48px', marginBottom: '8px' }}>⚠️</div>
          <h2 style={{ fontSize: '24px', fontWeight: '900', color: '#fbbf24', marginBottom: '8px' }}>Complete Your Account Setup</h2>
          <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.6)', maxWidth: '400px', margin: '0 auto 24px' }}>
            Your account was created but you haven't completed the payment setup yet. A valid credit card is required to activate your 7-day free trial.
          </p>
        </div>
        {error && (
          <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', textAlign: 'center', marginBottom: '16px', color: '#f87171', fontSize: '14px' }}>
            {error}
          </div>
        )}
        <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '12px', padding: '24px', textAlign: 'center' }}>
          <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '16px', lineHeight: '1.6' }}>
            💳 Enter your card via Stripe to start your <strong style={{ color: '#34d399' }}>7-day free trial</strong>.<br/>
            You won't be charged during the trial. Cancel anytime.
          </div>
          <button onClick={handleCompleteSetup} disabled={cancelLoading}
            style={{ background: 'linear-gradient(135deg, #059669, #047857)', border: 'none', borderRadius: '10px', padding: '14px 40px', color: 'white', fontSize: '16px', fontWeight: '800', cursor: cancelLoading ? 'wait' : 'pointer' }}>
            {cancelLoading ? 'Redirecting...' : '🔒 Complete Setup - Start Free Trial'}
          </button>
          <div style={{ marginTop: '16px', fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>Secure checkout powered by Stripe - €0 for 7 days, then €9.99/mo</div>
        </div>
        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <button onClick={onLogout} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline' }}>Sign out</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0', maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{ fontSize: '48px', marginBottom: '8px' }}>\ud83d\udc64</div>
        <h2 style={{ fontSize: '26px', fontWeight: '900', color: 'white', marginBottom: '4px' }}>My Account</h2>
        <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>Manage your subscription and account details</p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', textAlign: 'center', marginBottom: '16px', color: '#f87171', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {accountSettingsRequest && (
        <div style={{ background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.35)', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px' }}>
          <div style={{ color: '#93c5fd', fontSize: '13px', fontWeight: '700', marginBottom: '4px' }}>Email settings link</div>
          <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', lineHeight: '1.6' }}>
            Manage your daily email preference here, or close your account if you no longer want BetBudAI access.
          </div>
        </div>
      )}

      {/* Profile info */}
      <div style={cardStyle}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <div style={labelStyle}>Username</div>
            <div style={valueStyle}>{subStatus?.username || authUser?.username || '\u2014'}</div>
          </div>
          <div>
            <div style={labelStyle}>Full Name</div>
            <div style={valueStyle}>{subStatus?.full_name || authUser?.full_name || '\u2014'}</div>
          </div>
          <div>
            <div style={labelStyle}>Email</div>
            <div style={valueStyle}>{authUser?.email || '\u2014'}</div>
          </div>
          <div>
            <div style={labelStyle}>Member Since</div>
            <div style={valueStyle}>{subStatus?.joined_at ? new Date(subStatus.joined_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '\u2014'}</div>
          </div>
        </div>
      </div>

      {/* Subscription details */}
      <div style={{ ...cardStyle, border: `1px solid ${tierColor(tier)}33` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <div style={labelStyle}>Current Plan</div>
            <div style={{ fontSize: '20px', fontWeight: '900', color: tierColor(tier) }}>{tierLabel(tier)}</div>
          </div>
          <div style={{ background: isActive ? 'rgba(52,211,153,0.15)' : isCanceling ? 'rgba(251,191,36,0.15)' : 'rgba(255,255,255,0.08)', border: `1px solid ${isActive ? 'rgba(52,211,153,0.4)' : isCanceling ? 'rgba(251,191,36,0.4)' : 'rgba(255,255,255,0.15)'}`, borderRadius: '20px', padding: '4px 14px', fontSize: '12px', fontWeight: '700', color: isActive ? '#34d399' : isCanceling ? '#fbbf24' : 'rgba(255,255,255,0.4)' }}>
            {status === 'trialing' ? '\u23f3 Trial' : isActive ? '\u2713 Active' : isCanceling ? 'Canceling' : status || 'Inactive'}
          </div>
        </div>

        {status === 'trialing' && periodEnd && (
          <div style={{ background: 'rgba(52,211,153,0.11)', border: '1px solid rgba(52,211,153,0.35)', borderRadius: '8px', padding: '10px 14px', marginBottom: '14px' }}>
            <div style={{ color: '#34d399', fontSize: '13px', fontWeight: '700' }}>⏳ Trial active until {periodEnd}</div>
            <div style={{ color: 'rgba(255,255,255,0.62)', fontSize: '12px', marginTop: '4px' }}>
              {subStatus?.has_card
                ? `First ${monthlyPrice} charge is due on ${periodEnd} unless you cancel before then.`
                : `No card is on file. Add payment later if you want to continue on ${monthlyPrice}/mo after ${periodEnd}.`}
            </div>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={labelStyle}>Credit Card</div>
            <div style={{ ...valueStyle, color: subStatus?.has_card ? '#34d399' : '#f87171' }}>
              {subStatus?.has_card ? '\ud83d\udcb3 Added' : '\u274c Not Added'}
            </div>
          </div>
          <div>
            <div style={labelStyle}>Paid Subscriber</div>
            <div style={{ ...valueStyle, color: subStatus?.has_subscription ? '#34d399' : 'rgba(255,255,255,0.5)' }}>
              {subStatus?.has_subscription ? '\u2705 Yes' : '\u26aa No'}
            </div>
          </div>
          {tier !== 'free' && (
            <div>
              <div style={labelStyle}>Price</div>
              <div style={valueStyle}>{tier === 'vip' ? '\u20ac49.99/mo' : '\u20ac9.99/mo'}</div>
            </div>
          )}
          {periodEnd && (
            <div>
              <div style={labelStyle}>{isCanceling ? 'Access Until' : 'Next Billing Date'}</div>
              <div style={valueStyle}>{periodEnd}</div>
            </div>
          )}
        </div>

        {/* Cancel / status messages */}
        {isCanceling && (
          <div style={{ background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '8px', padding: '12px 16px', marginBottom: '12px' }}>
            <div style={{ color: '#fbbf24', fontSize: '13px', fontWeight: '600' }}>\u26a0\ufe0f Your subscription is set to cancel</div>
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', marginTop: '4px' }}>You\u2019ll keep full access until {periodEnd}. After that, your account will revert to the free tier.</div>
          </div>
        )}

        {cancelDone && (
          <div style={{ background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: '8px', padding: '12px 16px', marginBottom: '12px', color: '#34d399', fontSize: '13px', fontWeight: '600' }}>
            \u2713 Cancellation confirmed. You\u2019ll retain access until your billing period ends.
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {(isActive || status === 'trialing') && !isCanceling && subStatus?.has_subscription && (
            <button onClick={handleCancel} disabled={cancelLoading}
              style={{ flex: 1, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '8px', padding: '10px 20px', color: '#f87171', fontSize: '13px', fontWeight: '700', cursor: cancelLoading ? 'wait' : 'pointer' }}>
              {cancelLoading ? 'Canceling...' : '\u2716 Cancel Subscription'}
            </button>
          )}
          {tier === 'free' && !subStatus?.has_subscription && (
            <button onClick={() => window.location.hash = ''}
              style={{ flex: 1, background: 'linear-gradient(135deg, #6366f1, #7c3aed)', border: 'none', borderRadius: '8px', padding: '10px 20px', color: 'white', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>
              \ud83d\ude80 Upgrade to Premium
            </button>
          )}
        </div>
      </div>

      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <div>
            <div style={labelStyle}>Daily Picks Email</div>
            <div style={{ ...valueStyle, color: emailOptedOut ? '#fbbf24' : '#34d399' }}>
              {emailOptedOut ? 'Paused' : 'Subscribed'}
            </div>
          </div>
          <button onClick={() => handleDailyEmailPreference(!emailOptedOut)} disabled={emailPrefLoading}
            style={{ background: emailOptedOut ? 'rgba(52,211,153,0.12)' : 'rgba(251,191,36,0.12)', border: `1px solid ${emailOptedOut ? 'rgba(52,211,153,0.35)' : 'rgba(251,191,36,0.35)'}`, borderRadius: '8px', padding: '10px 18px', color: emailOptedOut ? '#34d399' : '#fbbf24', fontSize: '13px', fontWeight: '700', cursor: emailPrefLoading ? 'wait' : 'pointer' }}>
            {emailPrefLoading ? 'Saving...' : emailOptedOut ? 'Resume Daily Email' : 'Unsubscribe from Daily Email'}
          </button>
        </div>
        <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: '12px', lineHeight: '1.6' }}>
          This controls the 1:20pm picks-ready email only. It does not affect account, billing, or essential service emails.
        </div>
        {emailPrefMessage && <div style={{ color: '#93c5fd', fontSize: '12px', marginTop: '10px', fontWeight: '600' }}>{emailPrefMessage}</div>}
      </div>

      <div style={{ ...cardStyle, border: '1px solid rgba(239,68,68,0.28)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <div>
            <div style={labelStyle}>Close Account</div>
            <div style={{ ...valueStyle, color: '#f87171' }}>Permanent account closure</div>
          </div>
          <button onClick={handleCloseAccount} disabled={closeLoading || !canCloseAccount}
            style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '8px', padding: '10px 18px', color: '#f87171', fontSize: '13px', fontWeight: '700', cursor: closeLoading || !canCloseAccount ? 'not-allowed' : 'pointer', opacity: closeLoading || !canCloseAccount ? 0.55 : 1 }}>
            {closeLoading ? 'Closing...' : 'Close Account'}
          </button>
        </div>
        <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: '12px', lineHeight: '1.6' }}>
          Closing your account disables sign-in and stops daily emails. {canCloseAccount ? 'You can do this now.' : 'Cancel any active subscription first, then close the account.'}
        </div>
        {closeDone && <div style={{ color: '#34d399', fontSize: '12px', marginTop: '10px', fontWeight: '600' }}>Account closed. Signing you out...</div>}
      </div>

      {/* Sign out */}
      <div style={{ textAlign: 'center', marginTop: '24px' }}>
        <button onClick={onLogout} style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', padding: '10px 32px', color: 'rgba(255,255,255,0.6)', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
          Sign Out
        </button>
      </div>
      <LegalDisclaimerCard />
    </div>
  );
}

// ---- Top 4 Picks and Intraday (paid) — standalone card view showing ALL today's picks ----
function Top5PicksView() {
  const [allPicks, setAllPicks] = useState([]);
  const [watchlistPicks, setWatchlistPicks] = useState([]);
  const [droppedPicks, setDroppedPicks] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [releasePending, setReleasePending] = useState(null);
  const [cumulRoi, setCumulRoi] = useState(null);
  const [latestWinner5, setLatestWinner5] = useState(null);
  const [yesterdaySummary5, setYesterdaySummary5] = useState(null);
  const [yesterdayPicks5, setYesterdayPicks5] = useState([]);
  const [yesterdayDate5, setYesterdayDate5] = useState('');
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);
  const [now, setNow]           = useState(new Date());

  // Dublin-timezone-aware helpers — all time comparisons must use Dublin tz
  // to match displayed times (which use Europe/Dublin)
  const dublinNowStr = () => new Date().toLocaleString('sv-SE', { timeZone: 'Europe/Dublin' });
  const toDublinStr = (d) => d.toLocaleString('sv-SE', { timeZone: 'Europe/Dublin' });
  const parseRaceDate = (rt) => { if (!rt) return null; try { let s = rt.includes('T') ? rt : rt.replace(' ', 'T'); if (!s.endsWith('Z') && !s.includes('+')) s += 'Z'; const d = new Date(s); return isNaN(d.getTime()) ? null : d; } catch { return null; } };
  const dublinMinsToRace = (raceDate) => {
    // Compare in Dublin tz strings to avoid system-tz mismatch
    const nowDub = dublinNowStr();
    const raceDub = toDublinStr(raceDate);
    const nD = new Date(nowDub.replace(' ', 'T'));
    const rD = new Date(raceDub.replace(' ', 'T'));
    return (rD - nD) / 60000;
  };

  useEffect(() => { const t = setInterval(() => setNow(new Date()), 60000); return () => clearInterval(t); }, []);
  useEffect(() => { const h = () => setIsMobile(window.innerWidth < 768); window.addEventListener('resize', h); return () => window.removeEventListener('resize', h); }, []);
  useEffect(() => { loadPicks(); const iv = setInterval(() => { const h = new Date().getHours(); if (h >= 12 && h <= 18) loadPicks(); }, 30*60*1000); return () => clearInterval(iv); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/results/latest-winner`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/results/yesterday`).then(r => r.json()).catch(() => null),
    ])
      .then(([latestData, yesterdayData]) => {
        if (latestData?.success && latestData.fractional_odds) setLatestWinner5(latestData);
        if (yesterdayData?.success) {
          setYesterdaySummary5(yesterdayData.summary || null);
          setYesterdayPicks5(Array.isArray(yesterdayData.picks) ? yesterdayData.picks : []);
          setYesterdayDate5(yesterdayData.date || '');
        }
      })
      .catch(() => {});
  }, []);

  const loadPicks = async () => {
    setLoading(true); setError(null); setReleasePending(null);
    try {
      const [res, roiRes] = await Promise.all([
        fetch(API_BASE_URL + '/api/results/today'),
        fetch(API_BASE_URL + '/api/results/cumulative-roi'),
      ]);
      const data = await res.json();
      const roiData = await roiRes.json().catch(() => null);
      if (roiData?.success) setCumulRoi(roiData);
      if (data.success) {
        if (data.analysis_pending) {
          setReleasePending(data.pending_reason || 'Final checks still running');
        }

        const picks = (data.picks || []).filter(p => p.show_in_ui !== false);
        const watchlist = (data.watchlist || []).filter(p => p.is_watchlist === true || (p.pick_type === 'watchlist'));
        const dropped = (data.dropped || []).filter(p => p.is_dropped === true);
        // Assign rank by score (highest first)
        picks.sort((a, b) => parseFloat(b.comprehensive_score || b.score || 0) - parseFloat(a.comprehensive_score || a.score || 0));
        picks.forEach((p, i) => { p.originalRank = i + 1; });
        // Then sort by race time ascending (soonest first) — use Dublin tz strings for consistency
        picks.sort((a, b) => {
          const dA = parseRaceDate(a.race_time);
          const dB = parseRaceDate(b.race_time);
          const sA = dA ? toDublinStr(dA) : '9999';
          const sB = dB ? toDublinStr(dB) : '9999';
          return sA.localeCompare(sB);
        });
        watchlist.sort((a, b) => {
          const dA = parseRaceDate(a.race_time);
          const dB = parseRaceDate(b.race_time);
          const sA = dA ? toDublinStr(dA) : '9999';
          const sB = dB ? toDublinStr(dB) : '9999';
          return sA.localeCompare(sB);
        });
        dropped.sort((a, b) => {
          const dA = parseRaceDate(a.race_time);
          const dB = parseRaceDate(b.race_time);
          const sA = dA ? toDublinStr(dA) : '9999';
          const sB = dB ? toDublinStr(dB) : '9999';
          return sA.localeCompare(sB);
        });
        setAllPicks(picks);
        setWatchlistPicks(watchlist);
        setDroppedPicks(dropped);
      } else setError(data.error || 'Failed to load picks');
    } catch (err) { setError('Network error: ' + err.message); }
    finally { setLoading(false); }
  };

  const today = new Date().toLocaleDateString('en-GB', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
  const bannerData5 = buildPositiveBannerData(latestWinner5, yesterdaySummary5, yesterdayPicks5, yesterdayDate5);
  const totalPublishedPicks = allPicks.length + watchlistPicks.length;
  const displayPickCount = totalPublishedPicks || 4;
  const combinedPublishedPicks = [...allPicks, ...watchlistPicks];
  const winnersToday = combinedPublishedPicks.filter(p => {
    const oc = (p.outcome || '').toLowerCase();
    return oc === 'win' || oc === 'won';
  });

  const tierInfo = score => {
    const s = parseFloat(score || 0);
    if (s >= 95) return { bg:'#d97706', label:'ELITE' };
    if (s >= 90) return { bg:'#059669', label:'STRONG' };
    if (s >= 80) return { bg:'#3b82f6', label:'GOOD' };
    return { bg:'#0891b2', label:'VALUE' };
  };

  const formatRaceTime = rt => {
    if (!rt) return { date:'', time:'' };
    try {
      const d = new Date(rt.endsWith('Z') || rt.includes('+') ? rt : rt + 'Z');
      const tz = { timeZone:'Europe/Dublin' };
      return {
        date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', year:'numeric', ...tz }),
        time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12:false, ...tz }),
      };
    } catch { return { date: rt.substring(0,10), time: rt.substring(11,16) }; }
  };

  const formatDroppedMeta = (pick) => {
    const rawDropTs = pick?.dropped_at || pick?.drop_time || pick?.updated_at;
    let droppedAt = null;
    if (rawDropTs) {
      try {
        const parsed = new Date(rawDropTs);
        if (!isNaN(parsed.getTime())) {
          droppedAt = parsed.toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Europe/Dublin',
          });
        }
      } catch {
        droppedAt = null;
      }
    }
    const reason = (pick?.drop_reason || pick?.removal_reason || pick?.drop_note || '').toString().trim();
    return {
      droppedAt: droppedAt || '--:--',
      reason: reason || 'Live re-analysis pulled this selection',
    };
  };

  const bettingWindow = (pick) => {
    if (!pick.race_time) return { label:'Anytime Today', desc:'Long price — odds stable', bg:'rgba(59,130,246,0.12)', border:'rgba(59,130,246,0.4)', color:'#60a5fa' };
    try {
      const raceDate = parseRaceDate(pick.race_time);
      if (!raceDate) return { label:'Anytime Today', desc:'', bg:'rgba(59,130,246,0.12)', border:'rgba(59,130,246,0.4)', color:'#60a5fa' };
      const minsToRace = dublinMinsToRace(raceDate);
      if (minsToRace < 0) return { label:'Race Complete', desc:'Check results', bg:'rgba(107,114,128,0.12)', border:'rgba(107,114,128,0.4)', color:'#9ca3af' };
      if (minsToRace < 15) return { label:'🔥 Bet Now', desc:'Race imminent', bg:'rgba(239,68,68,0.15)', border:'rgba(239,68,68,0.5)', color:'#ef4444' };
      if (minsToRace < 120) return { label:'⏰ 1-2hrs Before', desc:'Price stable until near off', bg:'rgba(234,179,8,0.12)', border:'rgba(234,179,8,0.4)', color:'#eab308' };
      return { label:'🏦 Anytime Today', desc:'Long price — odds stable', bg:'rgba(59,130,246,0.12)', border:'rgba(59,130,246,0.4)', color:'#60a5fa' };
    } catch { return { label:'Anytime Today', desc:'', bg:'rgba(59,130,246,0.12)', border:'rgba(59,130,246,0.4)', color:'#60a5fa' }; }
  };

  const normOutcome = p => normalizePickOutcome(p) || null;
  const outcomeStyle = o => {
    if (o === 'WIN')    return { bg:'#059669', text:'WIN ✓' };
    if (o === 'PLACED') return { bg:'#3b82f6', text:'PLACED' };
    if (o === 'LOSS')   return { bg:'#ef4444', text:'LOSS ✗' };
    return { bg:'#6b7280', text:'PENDING ⏳' };
  };

  if (loading) return <div style={{ textAlign:'center', padding:'60px 20px', color:'white' }}><div style={{ fontSize:'18px', opacity:0.8 }}>Loading all picks...</div></div>;
  if (error) return <div style={{ background:'rgba(239,68,68,0.15)', border:'1px solid #ef4444', borderRadius:'10px', padding:'24px', textAlign:'center', color:'white' }}><div style={{ fontWeight:'700', marginBottom:'6px' }}>Error loading picks</div><div style={{ fontSize:'13px', opacity:0.8, marginBottom:'16px' }}>{error}</div><button onClick={loadPicks} style={{ background:'#059669', border:'none', borderRadius:'6px', color:'white', padding:'8px 20px', cursor:'pointer', fontWeight:'700' }}>Retry</button></div>;

  // Don't reveal picks until 1pm Dublin time — selections may change as new info arrives
  const dublinHour5 = parseInt(now.toLocaleString('en-GB', { hour:'numeric', hour12:false, timeZone:'Europe/Dublin' }));
  if (dublinHour5 < 13) return (
    <div style={{ textAlign:'center', padding:'60px 20px' }}>
      <div style={{ fontSize:'48px', marginBottom:'16px' }}>🏆</div>
      <div style={{ fontSize:'20px', fontWeight:'800', color:'white', marginBottom:'8px' }}>Top {displayPickCount} Picks and Intraday</div>
      <div style={{ fontSize:'15px', color:'rgba(255,255,255,0.7)', lineHeight:'1.7' }}>Today's official picks are finalised and published at <strong style={{ color:'#a78bfa' }}>1:00pm</strong>. Most days include <strong>{displayPickCount}</strong> total picks (4 official + up to 2 watchlist).</div>
      <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.45)', marginTop:'12px' }}>Our AI is analysing today's races, odds, going and form data.<br/>Check back after 1pm for your full selections.</div>
      <div style={{ marginTop:'14px', fontSize:'12px', color:'rgba(255,255,255,0.55)', lineHeight:'1.6' }}>A daily email is sent around 1:20pm to your profile email once picks are settled, including results in the format winners out of total picks. Research and educational purposes only. BetBudAI is not a betting site, not a bookmaker, and not financial or betting advice. Always bet responsibly and only risk what you can afford to lose.</div>
    </div>
  );

  return (
    <div>
      {/* Latest Winner Banner */}
      {(bannerData5.horse || bannerData5.odds || bannerData5.summaryText) && (
        <div style={{
          maxWidth: '100%', margin: '0 0 16px', padding: isMobile ? '10px 12px' : '12px 20px',
          background: 'linear-gradient(135deg, rgba(52,211,153,0.12), rgba(16,185,129,0.06))',
          border: '1px solid rgba(52,211,153,0.3)', borderRadius: '12px',
          display: 'flex', alignItems: 'center', justifyContent: isMobile ? 'flex-start' : 'center', gap: isMobile ? '7px' : '10px',
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: '10px', fontWeight: '800', color: '#34d399', background: 'rgba(5,150,105,0.18)', border: '1px solid rgba(52,211,153,0.35)', padding: '2px 8px', borderRadius: '999px', letterSpacing: '0.6px' }}>LIVE SNAPSHOT</span>
          <span style={{ fontSize: isMobile ? '18px' : '22px' }}>🏆</span>
          <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: isMobile ? '12px' : '14px', fontWeight: '600', lineHeight: isMobile ? '1.45' : '1.35', textAlign: isMobile ? 'left' : 'center' }}>
            Top example: {bannerData5.horse ? <><span style={{ color: '#fbbf24', fontWeight: '900' }}>{bannerData5.horse}</span> won{bannerData5.odds ? ' at ' : ' '}</> : 'our AI value model keeps surfacing strong opportunities'}
            {bannerData5.odds && <span style={{ color: '#34d399', fontWeight: '900', fontSize: '16px' }}>{bannerData5.odds}</span>} {bannerData5.horse ? bannerData5.label : ''}.
            <span style={{ marginLeft: '6px' }}>
              {bannerData5.summaryMode === 'yesterday'
                ? <>{`Yesterday (${bannerData5.yesterdayLabel}): `}<span style={{ color: '#fbbf24', fontWeight: '900' }}>{Number(yesterdaySummary5?.wins || 0)} winner{Number(yesterdaySummary5?.wins || 0) === 1 ? '' : 's'}</span>{' & '}<span style={{ color: '#60a5fa', fontWeight: '900' }}>{Number(yesterdaySummary5?.places || 0)} placed</span>{` out of ${Number(yesterdaySummary5?.total_picks || 0)}.`}</>
                : bannerData5.summaryText}
            </span>
          </span>
          <span style={{ fontSize: isMobile ? '12px' : '14px' }}>🔥</span>
        </div>
      )}

      {/* Header */}
      <div style={{ background:'linear-gradient(135deg,#1e3a5f 0%,#7c3aed 50%,#1e3a5f 100%)', border:'2px solid #a78bfa', borderRadius:'14px', padding: isMobile ? '16px 14px' : '22px 28px', marginBottom:'20px', color:'white', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div style={{ fontSize:'13px', textTransform:'uppercase', letterSpacing:'1px', color:'#c4b5fd', opacity:0.9 }}>Premium · All Daily Picks</div>
          <div style={{ fontSize: isMobile ? '20px' : '24px', fontWeight:'900', marginTop:'4px' }}>🏆 Top {displayPickCount} Picks and Intraday</div>
          <div style={{ fontSize:'13px', opacity:0.75, marginTop:'4px' }}>{today}</div>
        </div>
        <button onClick={loadPicks} style={{ background:'rgba(255,255,255,0.15)', border:'1px solid rgba(255,255,255,0.4)', borderRadius:'8px', color:'white', padding:'8px 18px', cursor:'pointer', fontSize:'13px', fontWeight:'600' }}>Refresh</button>
      </div>

      <div style={{ background:'rgba(59,130,246,0.10)', border:'1px solid rgba(96,165,250,0.35)', borderRadius:'10px', padding:'11px 14px', marginBottom:'16px' }}>
        <div style={{ color:'#93c5fd', fontSize:'13px', fontWeight:'700' }}>Email update around 1:20pm</div>
        <div style={{ color:'rgba(255,255,255,0.68)', fontSize:'12px', lineHeight:'1.6', marginTop:'4px' }}>
          Once today's picks are settled, we send a daily "picks ready" email to your profile email with a link back to BetBudAI and a winners-out-of-total summary (for example 4 out of 6). Selections can still change in exceptional race-day cases (for example non-runners, late market shifts, or late data updates), so always re-check this page before betting. Research and educational purposes only. BetBudAI is not a betting site. Always bet responsibly.
        </div>
      </div>

      {/* Today's Winners Banner */}
      {(() => {
        const winners = winnersToday;
        if (winners.length === 0) return null;
        const toFrac = (dec) => { const d = parseFloat(dec); if (!d || d <= 1) return null; const n = d - 1; const denom = 10; const num = Math.round(n * denom); const gcd = (a,b) => b ? gcd(b, a%b) : a; const g = gcd(num, denom); return `${num/g}/${denom/g}`; };
        return (
          <div style={{ background:'linear-gradient(135deg, rgba(5,150,105,0.25) 0%, rgba(16,185,129,0.15) 100%)', border:'2px solid rgba(52,211,153,0.6)', borderRadius:'12px', padding:'14px 18px', marginBottom:'16px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'10px' }}>
              <span style={{ fontSize:'22px' }}>🔥</span>
              <span style={{ color:'#34d399', fontWeight:'900', fontSize:'16px', letterSpacing:'0.5px' }}>{winners.length} Winner{winners.length > 1 ? 's' : ''} Today! ({winners.length}/{Math.max(1, totalPublishedPicks)} picks)</span>
              <span style={{ marginLeft:'auto', fontSize:'11px', color:'rgba(255,255,255,0.45)', fontWeight:'600', textTransform:'uppercase', letterSpacing:'0.8px' }}>Live Results</span>
            </div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:'8px' }}>
              {winners.map((w, i) => {
                const odds = w.sp_odds ? parseFloat(w.sp_odds) : parseFloat(w.odds || 0);
                const oddsStr = toFrac(odds);
                return (
                  <div key={i} style={{ background:'rgba(16,185,129,0.2)', border:'1px solid rgba(52,211,153,0.5)', borderRadius:'10px', padding:'8px 14px', display:'flex', alignItems:'center', gap:'8px' }}>
                    <span style={{ fontSize:'16px' }}>🏇</span>
                    <div>
                      <div style={{ color:'white', fontWeight:'800', fontSize:'14px' }}>{w.horse}</div>
                      <div style={{ color:'rgba(255,255,255,0.6)', fontSize:'11px', marginTop:'1px' }}>
                        {w.course && <span>{w.course}</span>}
                        {oddsStr && <span style={{ color:'#34d399', fontWeight:'700', marginLeft: w.course ? '6px' : '0' }}>@ {oddsStr}</span>}
                      </div>
                    </div>
                    <span style={{ background:'#059669', color:'white', fontSize:'11px', fontWeight:'800', padding:'2px 8px', borderRadius:'6px', marginLeft:'4px' }}>WON ✓</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* ROI */}
      {cumulRoi?.success && (() => {
        const rv = cumulRoi.roi ?? 0; const rs = cumulRoi.settled || 0;
        return (
          <div style={{ background: rv >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.13)', border: `1.5px solid ${rv >= 0 ? 'rgba(16,185,129,0.45)' : 'rgba(239,68,68,0.4)'}`, borderRadius:'14px', padding: isMobile ? '14px 16px' : '18px 24px', marginBottom:'20px', display:'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', justifyContent:'space-between', gap:'12px' }}>
            <div style={{ display:'flex', alignItems:'center', gap: isMobile ? '14px' : '20px' }}>
              <div style={{ fontSize: isMobile ? '28px' : '38px' }}>💰</div>
              <div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'1.2px', fontWeight:'700', marginBottom:'4px' }}>Return on Investment</div>
                <div style={{ fontSize: isMobile ? '26px' : '40px', fontWeight:'900', color: rv >= 0 ? '#34d399' : '#f87171', lineHeight:1 }}>{rv >= 0 ? '+' : ''}{rv.toFixed(1)}%</div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'4px' }}>Since 22 Mar · {rs} settled</div>
              </div>
            </div>
            <div style={{ textAlign: isMobile ? 'left' : 'right' }}>
              <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)', lineHeight:'1.6' }}>
                Every €1 staked returned <span style={{ color: rv >= 0 ? '#34d399' : '#f87171', fontWeight:'700' }}>€{(1 + rv / 100).toFixed(2)}</span> on average
              </div>
              <div style={{ marginTop:'8px' }}>
                <span onClick={() => { fetch(API_BASE_URL + '/api/results/export-csv').then(r => r.text()).then(csv => { const blob = new Blob([csv], { type: 'text/csv' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'BetBudAI_ROI_Data.csv'; a.click(); URL.revokeObjectURL(url); }).catch(() => {}); }}
                  style={{ cursor:'pointer', fontSize:'12px', fontWeight:'700', color:'white', background:'linear-gradient(135deg,#059669,#047857)', border:'none', borderRadius:'8px', padding:'8px 18px', display:'inline-flex', alignItems:'center', gap:'6px' }}>
                  📥 Download Full History CSV
                </span>
              </div>
            </div>
          </div>
        );
      })()}

      {releasePending && (
        <div style={{ background:'rgba(245,158,11,0.14)', border:'1px solid rgba(245,158,11,0.4)', borderRadius:'10px', padding:'12px 14px', marginBottom:'14px' }}>
          <div style={{ color:'#f59e0b', fontSize:'13px', fontWeight:'700' }}>⏳ Final checks in progress</div>
          <div style={{ color:'rgba(255,255,255,0.7)', fontSize:'12px', marginTop:'4px' }}>{releasePending}</div>
        </div>
      )}

      {/* Official Picks */}
      {(() => {
        const officialPicksAll = allPicks.filter(p => !p.is_dropped);
        const upcomingOfficialPicks = officialPicksAll.filter(p => {
          const rd = parseRaceDate(p.race_time);
          if (!rd) return true;
          return dublinMinsToRace(rd) > 0;
        });
        return upcomingOfficialPicks.length === 0;
      })() ? (
        <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'12px', padding:'48px 24px', textAlign:'center', color:'rgba(255,255,255,0.7)' }}>
          <div style={{ fontSize:'18px', fontWeight:'700', color:'white', marginBottom:'8px' }}>No upcoming official picks</div>
          <div style={{ fontSize:'14px' }}>All official selections have now started or finished for today.</div>
        </div>
      ) : (() => {
        const officialPicksAll = allPicks.filter(p => !p.is_dropped);
        const upcomingPicks = officialPicksAll.filter(p => {
          const rd = parseRaceDate(p.race_time);
          if (!rd) return true;
          return dublinMinsToRace(rd) > 0;
        });
        const upcomingCount = upcomingPicks.length;

        const renderPickCard = (pick, idx) => {
            const tier = tierInfo(pick.comprehensive_score || pick.score);
            const rank = pick.originalRank || (idx + 1);
            const rankColors = { 1:'#d97706', 2:'#6b7280', 3:'#92400e', 4:'#0891b2', 5:'#7c3aed', 6:'#dc2626' };
            const ft = formatRaceTime(pick.race_time);
            const bw = bettingWindow(pick);
            const outcome = normOutcome(pick);
            const oc = outcomeStyle(outcome);
            return (
              <div key={idx} style={{ background:'white', borderRadius:'12px', padding: isMobile ? '14px 12px' : '20px 22px', borderLeft:`5px solid ${rankColors[rank] || tier.bg}`, boxShadow:'0 2px 12px rgba(0,0,0,0.1)' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'8px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                    <div style={{ background: rankColors[rank] || tier.bg, color:'white', borderRadius:'8px', padding:'6px 10px', textAlign:'center', minWidth:'44px' }}>
                      <div style={{ fontSize:'18px', fontWeight:'900' }}>#{rank}</div>
                      <div style={{ fontSize:'9px', fontWeight:'700', opacity:0.85, textTransform:'uppercase', lineHeight:'1' }}>Pick</div>
                    </div>
                    <div>
                      <div style={{ fontSize: isMobile ? '17px' : '20px', fontWeight:'800', color:'#111' }}>
                        {pick.horse || 'Unknown'}
                        {pick.is_hot_prospect && <span style={{ background:'linear-gradient(135deg,#dc2626,#f59e0b)', color:'white', fontSize:'10px', fontWeight:'800', padding:'2px 8px', borderRadius:'5px', marginLeft:'8px', verticalAlign:'middle', letterSpacing:'0.5px' }}>🔥 HOT PROSPECT</span>}
                        {pick.pick_type === 'watchlist' && <span style={{ background:'linear-gradient(135deg,#1d4ed8,#2563eb)', color:'white', fontSize:'10px', fontWeight:'800', padding:'2px 8px', borderRadius:'5px', marginLeft:'8px', verticalAlign:'middle', letterSpacing:'0.5px' }}>👀 WATCHLIST</span>}
                      </div>
                      <div style={{ display:'flex', flexWrap:'wrap', gap:'6px', marginTop:'6px', alignItems:'center' }}>
                        {pick.course && <span style={{ background:'#1e3a5f', color:'white', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'700' }}>{pick.course}</span>}
                        {ft.date && <span style={{ background:'#f3f4f6', color:'#374151', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'600' }}>{ft.date}</span>}
                        {ft.time && <span style={{ background:'#ecfdf5', color:'#065f46', padding:'3px 10px', borderRadius:'6px', fontSize:'12px', fontWeight:'700', border:'1px solid #a7f3d0' }}>{ft.time}</span>}
                      </div>
                    </div>
                  </div>
                  <div style={{ display:'flex', gap:'8px', alignItems:'center' }}>
                    {outcome && (
                      <span style={{ background: oc.bg, color:'white', padding:'5px 12px', borderRadius:'8px', fontSize:'12px', fontWeight:'800' }}>{oc.text}</span>
                    )}
                    {pick.odds && (
                      <div style={{ textAlign:'center' }}>
                        <div style={{ background:'#1e3a5f', color:'white', padding:'5px 14px', borderRadius:'8px', fontWeight:'900', fontSize:'22px' }}>{toFractional(pick.odds)}</div>
                        <div style={{ fontSize:'10px', color:'#6b7280', marginTop:'2px', fontWeight:'600' }}>ODDS</div>
                      </div>
                    )}
                    {pick.odds && parseFloat(pick.odds) <= 1.7 && (
                      <span style={{ background:'#fef3c7', color:'#92400e', border:'1px solid #fbbf24', borderRadius:'6px', padding:'4px 8px', fontSize:'11px', fontWeight:'700' }}>⚠ Low Odds Value</span>
                    )}
                    <span style={{ background: tier.bg, color:'white', padding:'5px 12px', borderRadius:'8px', fontSize:'12px', fontWeight:'700' }}>{tier.label}</span>
                  </div>
                </div>
                {/* Betting window */}
                <div style={{ marginTop:'10px', display:'inline-flex', alignItems:'center', gap:'6px', background: bw.bg, border:`1px solid ${bw.border}`, borderRadius:'7px', padding:'5px 12px' }}>
                  <span style={{ fontSize:'13px', fontWeight:'800', color: bw.color }}>{bw.label}</span>
                  <span style={{ fontSize:'11px', color:'#6b7280' }}>— {bw.desc}</span>
                </div>
                {/* Trainer / Jockey / Form */}
                <div style={{ fontSize:'13px', color:'#374151', marginTop:'12px', display:'flex', gap:'18px', flexWrap:'wrap', alignItems:'center' }}>
                  {pick.trainer && <span><strong>Trainer:</strong> {pick.trainer}</span>}
                  {pick.jockey && <span><strong>Jockey:</strong> {pick.jockey}</span>}
                  {pick.form && <span style={{ background:'#f3f4f6', borderRadius:'5px', padding:'2px 8px', fontFamily:'monospace', fontWeight:'700', color:'#1e3a5f', letterSpacing:'1px' }}>Form: {pick.form}</span>}
                  {renderScoreGapBadge(pick.score_gap)}
                </div>
                {/* Score badge */}
                {(() => {
                  const score = parseFloat(pick.comprehensive_score || pick.score || 0);
                  if (!score) return null;
                  return (
                    <div style={{ marginTop:'10px', padding:'10px 14px', background:`${tier.bg}18`, borderRadius:'8px', borderLeft:`3px solid ${tier.bg}` }}>
                      <span style={{ background: tier.bg, color:'white', borderRadius:'5px', padding:'2px 9px', fontSize:'11px', fontWeight:'800' }}>{tier.label}</span>
                      <span style={{ fontSize:'12px', fontWeight:'700', color:'#1e3a5f', marginLeft:'8px' }}>Score: {score.toFixed(0)}</span>
                    </div>
                  );
                })()}
                {/* Result analysis */}
                {outcome && pick.result_analysis && (
                  <div style={{ marginTop:'10px', padding:'10px 14px', background:'rgba(0,0,0,0.03)', borderRadius:'8px', fontSize:'12px', color:'#374151', lineHeight:'1.5' }}>
                    <strong>Analysis:</strong> {pick.result_analysis}
                    {pick.result_winner_name && pick.result_winner_name !== pick.horse && (
                      <div style={{ marginTop:'4px', color:'#ef4444', fontWeight:'700' }}>Winner: {pick.result_winner_name}</div>
                    )}
                  </div>
                )}
              </div>
            );
        };

        return (
        <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>
          <div style={{ background:'rgba(16,185,129,0.10)', border:'1px solid rgba(16,185,129,0.35)', borderRadius:'10px', padding:'10px 14px' }}>
            <div style={{ fontSize:'13px', fontWeight:'700', color:'#34d399' }}>✅ Official Picks ({upcomingCount})</div>
            <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.6)', marginTop:'4px' }}>These are the bettable selections that have not started yet. They are not replaced by watchlist items.</div>
          </div>
          {upcomingPicks.length > 0 && (
            <>
              <div style={{ marginTop:'8px', padding:'10px 16px', background:'rgba(16,185,129,0.08)', border:'1px solid rgba(16,185,129,0.25)', borderRadius:'10px' }}>
                <div style={{ fontSize:'13px', fontWeight:'700', color:'#34d399' }}>🟢 Upcoming ({upcomingPicks.length})</div>
                <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>Races that have not started yet.</div>
              </div>
              {upcomingPicks.map((pick, idx) => renderPickCard(pick, idx))}
            </>
          )}

          {/* Watchlist picks */}
          {watchlistPicks.length > 0 && (
            <>
              <div style={{ marginTop:'8px', padding:'10px 16px', background:'rgba(59,130,246,0.10)', border:'1px solid rgba(59,130,246,0.30)', borderRadius:'10px' }}>
                <div style={{ fontSize:'13px', fontWeight:'700', color:'#60a5fa' }}>👀 Watchlist ({watchlistPicks.length})</div>
                <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>Monitoring candidates only. Do not replace official picks with these.</div>
              </div>
              {watchlistPicks.map((pick, idx) => {
                const ft = formatRaceTime(pick.race_time);
                const tier = tierInfo(pick.comprehensive_score || pick.score);
                return (
                  <div key={'watch-'+idx} style={{ background:'rgba(255,255,255,0.92)', borderRadius:'12px', padding: isMobile ? '12px 10px' : '16px 18px', borderLeft:'5px solid #3b82f6', boxShadow:'0 1px 6px rgba(0,0,0,0.06)' }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'8px' }}>
                      <div>
                        <div style={{ fontSize: isMobile ? '15px' : '17px', fontWeight:'800', color:'#1f2937' }}>{pick.horse || 'Unknown'}</div>
                        <div style={{ display:'flex', flexWrap:'wrap', gap:'6px', marginTop:'4px', alignItems:'center' }}>
                          {pick.course && <span style={{ background:'#dbeafe', color:'#1e3a8a', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'600' }}>{pick.course}</span>}
                          {ft.time && <span style={{ background:'#eff6ff', color:'#1d4ed8', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'600' }}>{ft.time}</span>}
                          <span style={{ background:'#1d4ed8', color:'white', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'700' }}>W{pick.watchlist_rank || (idx + 1)}</span>
                          <span style={{ background:tier.bg, color:'white', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'700' }}>{tier.label}</span>
                        </div>
                      </div>
                      <span style={{ background:'#2563eb', color:'white', padding:'4px 10px', borderRadius:'6px', fontSize:'11px', fontWeight:'800' }}>WATCHLIST</span>
                    </div>
                  </div>
                );
              })}
            </>
          )}

          {/* Dropped picks */}
          {droppedPicks.length > 0 && (
            <>
              <div style={{ marginTop:'8px', padding:'10px 16px', background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.25)', borderRadius:'10px' }}>
                <div style={{ fontSize:'13px', fontWeight:'700', color:'#f87171' }}>⚠ Selections Removed</div>
                <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>The following picks were dropped after re-analysis — odds or form changed unfavourably.</div>
              </div>
              {droppedPicks.map((pick, idx) => {
                const ft = formatRaceTime(pick.race_time);
                const dropMeta = formatDroppedMeta(pick);
                return (
                  <div key={'dropped-'+idx} style={{ background:'#f3f4f6', borderRadius:'12px', padding: isMobile ? '12px 10px' : '16px 18px', borderLeft:'5px solid #9ca3af', boxShadow:'0 1px 6px rgba(0,0,0,0.06)', opacity:0.7 }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'8px' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                        <div style={{ background:'#9ca3af', color:'white', borderRadius:'8px', padding:'6px 10px', textAlign:'center', minWidth:'44px' }}>
                          <div style={{ fontSize:'14px', fontWeight:'900' }}>✗</div>
                          <div style={{ fontSize:'8px', fontWeight:'700', opacity:0.85, textTransform:'uppercase', lineHeight:'1' }}>Dropped</div>
                        </div>
                        <div>
                          <div style={{ fontSize: isMobile ? '15px' : '17px', fontWeight:'700', color:'#6b7280', textDecoration:'line-through' }}>{pick.horse || 'Unknown'}</div>
                          <div style={{ display:'flex', flexWrap:'wrap', gap:'6px', marginTop:'4px', alignItems:'center' }}>
                            {pick.course && <span style={{ background:'#d1d5db', color:'#374151', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'600' }}>{pick.course}</span>}
                            {ft.time && <span style={{ background:'#e5e7eb', color:'#6b7280', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'600' }}>{ft.time}</span>}
                          </div>
                        </div>
                      </div>
                      <span style={{ background:'#ef4444', color:'white', padding:'4px 10px', borderRadius:'6px', fontSize:'11px', fontWeight:'800' }}>NO LONGER SELECTED</span>
                    </div>
                    <div style={{ marginTop:'8px', fontSize:'12px', color:'#9ca3af', fontStyle:'italic' }}>This pick was removed during live re-analysis — do not bet.</div>
                    <div style={{ marginTop:'6px', fontSize:'12px', color:'#b91c1c', fontWeight:'700' }}>Dropped at {dropMeta.droppedAt} • {dropMeta.reason}</div>
                  </div>
                );
              })}
            </>
          )}
        </div>
        );
      })()}

      {/* Analysis Quality Report */}
      <AnalysisQualityReport date={new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' })} />

      <div style={{ marginTop:'28px', padding:'16px 20px', background:'rgba(255,255,255,0.07)', borderRadius:'10px', color:'rgba(255,255,255,0.6)', fontSize:'12px', textAlign:'center', lineHeight:'1.6' }}>
        All daily picks · Results update automatically after each race · Research and education tool only (not a betting site) · Always bet responsibly.
      </div>
      <LegalDisclaimerCard />
    </div>
  );
}

// ---- Analysis Quality Report ----
function AnalysisQualityReport({ date }) {
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);

  useEffect(() => {
    if (!date) return;

    fetch(`${API_BASE_URL}/api/picks/analysis-quality?date=${date}`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          setQuality(data);
        }
      })
      .catch(err => console.error('Quality check error:', err))
      .finally(() => setLoading(false));
  }, [date]);

  if (loading || !quality || quality.status === 'NO_ANALYSIS') return null;

  const statusColors = {
    'EXCELLENT': { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.45)', text: '#34d399' },
    'GOOD': { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.45)', text: '#60a5fa' },
    'PARTIAL': { bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.45)', text: '#fbbf24' },
    'INCOMPLETE': { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.45)', text: '#f87171' }
  };

  const colors = statusColors[quality.status] || statusColors['PARTIAL'];

  return (
    <div style={{
      marginTop: '24px',
      background: colors.bg,
      border: `2px solid ${colors.border}`,
      borderRadius: '12px',
      padding: isMobile ? '14px 16px' : '18px 24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ fontSize: '24px' }}>✅</div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>Analysis Quality Check</div>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)', marginTop: '2px' }}>
              {quality.summary.total_horses_analyzed} horses analyzed · {quality.summary.ui_picks_selected} picks selected
            </div>
          </div>
        </div>
        <div style={{
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: '999px',
          padding: '6px 14px',
          fontSize: '12px',
          fontWeight: '800',
          color: colors.text,
          letterSpacing: '0.5px'
        }}>
          {quality.status}
        </div>
      </div>

      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '8px',
        padding: isMobile ? '12px' : '14px',
        marginBottom: '12px'
      }}>
        <div style={{ fontSize: '14px', fontWeight: '700', color: colors.text, marginBottom: '8px' }}>
          {quality.verdict}
        </div>
        {quality.checks && quality.checks.length > 0 && (
          <div style={{ display: 'grid', gap: '6px' }}>
            {quality.checks.map((check, idx) => (
              <div key={idx} style={{
                fontSize: '12px',
                color: 'rgba(255,255,255,0.85)',
                lineHeight: '1.5',
                paddingLeft: '4px'
              }}>
                {check}
              </div>
            ))}
          </div>
        )}
      </div>

      {quality.data_completeness && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(3, 1fr)', gap: '8px' }}>
          {Object.entries(quality.data_completeness).map(([field, data]) => (
            <div key={field} style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '6px',
              padding: '8px 10px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', fontWeight: '700' }}>
                {field.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>
                {data.percentage.toFixed(0)}%
              </div>
              <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.45)' }}>
                {data.count}/{quality.summary.total_horses_analyzed}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---- Yesterday's Results ----
function YesterdayResultsView({ isFreeUser }) {
  const [results, setResults]         = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [isMobile, setIsMobile]       = useState(typeof window !== 'undefined' && window.innerWidth < 768);
  const [cumulRoi, setCumulRoi]         = useState(null);
  const [layData,  setLayData]          = useState(null);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (isFreeUser) {
      setLoading(false);
      return;
    }
    loadResults();
  }, [isFreeUser]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadResults = async () => {
    setLoading(true); setError(null);
    try {
      const [todayRes, yestRes, cumulRes] = await Promise.all([
        fetch(API_BASE_URL + '/api/results/today'),
        fetch(API_BASE_URL + '/api/results/yesterday'),
        fetch(API_BASE_URL + '/api/results/cumulative-roi'),
      ]);
      const [todayData, yestData, cumulData] = await Promise.all([todayRes.json(), yestRes.json(), cumulRes.json()]);
      if (cumulData.success) setCumulRoi(cumulData);

      const todayPicks = (todayData.success ? todayData.picks || [] : [])
        .map(p => ({ ...p, _dayLabel: 'Today' }));
      const yestPicks  = (yestData.success  ? yestData.picks  || [] : []).map(p => ({ ...p, _dayLabel: 'Yesterday' }));
      const todayDropped = (todayData.success ? todayData.dropped || [] : [])
        .map(p => ({ ...p, _dayLabel: 'Today', is_dropped: true }));
      const yestDropped = (yestData.success ? yestData.dropped || [] : [])
        .map(p => ({ ...p, _dayLabel: 'Yesterday', is_dropped: true }));
      // Dropped picks are intentionally excluded from the results list
      void todayDropped; void yestDropped;
      // Deduplicate: same course + race_time[:16] => keep highest-scored version
      // Use course+time (not horse name) to handle name variants like apostrophes
      const deduped = {};
      [...todayPicks, ...yestPicks].forEach(p => {
        const rt = (p.race_time || '').substring(0, 16);
        const key = (p.course || p.race_course || '') + '|' + rt;
        const sc  = parseFloat(p.comprehensive_score || p.analysis_score || 0);
        if (!deduped[key] || sc > parseFloat(deduped[key].comprehensive_score || deduped[key].analysis_score || 0)) {
          deduped[key] = p;
        }
      });
      const dedupedDropped = {};
      const activePicks = Object.values(deduped).filter(p => !p.is_dropped);
      const droppedPicks = [];
      void dedupedDropped;
      const allPicks = [...activePicks];

      const allRaceFields = { ...(yestData.race_fields || {}), ...(todayData.race_fields || {}) }; // eslint-disable-line no-unused-vars

      const ts = todayData.success ? (todayData.summary || {}) : {};
      const ys = yestData.success  ? (yestData.summary  || {}) : {};
      const combinedSummary = {
        total_picks:  (ts.total_picks  || 0) + (ys.total_picks  || 0),
        wins:         (ts.wins         || 0) + (ys.wins         || 0),
        places:       (ts.places       || 0) + (ys.places       || 0),
        losses:       (ts.losses       || 0) + (ys.losses       || 0),
        pending:      (ts.pending      || 0) + (ys.pending      || 0),
        profit:       (ts.profit       || 0) + (ys.profit       || 0),
        total_stake:  (ts.total_stake  || 0) + (ys.total_stake  || 0),
      };
      // ROI = profit / total_stake * 100  (standard financial ROI)
      combinedSummary.roi = combinedSummary.total_stake > 0
        ? (combinedSummary.profit / combinedSummary.total_stake * 100) : 0;

      // Recompute summary from deduplicated picks (more accurate than API summaries)
      const normOc = p => { const re = (p.result_emoji||''); const oc = (p.outcome||'').toLowerCase(); if(re==='\u2705'||oc==='win'||oc==='won') return 'WIN'; if(re==='\uD83D\uDD35'||oc==='placed') return 'PLACED'; if(re==='\u274C'||oc==='loss'||oc==='lost') return 'LOSS'; return ''; };
      const settled = activePicks.filter(p => ['WIN','PLACED','LOSS'].includes(normOc(p)));
      const recomputed = {
        total_picks: activePicks.length,
        wins:    settled.filter(p => normOc(p) === 'WIN').length,
        places:  settled.filter(p => normOc(p) === 'PLACED').length,
        losses:  settled.filter(p => normOc(p) === 'LOSS').length,
        pending: activePicks.length - settled.length,
        removed: droppedPicks.length,
        profit:  combinedSummary.profit,
        total_stake: combinedSummary.total_stake,
        roi: combinedSummary.roi,
      };
      if (allPicks.length === 0 && !todayData.success && !yestData.success) {
        setError('Failed to load results');
      } else {
        setResults({ picks: allPicks, summary: recomputed });
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
    // Lay analysis — non-critical, silent fail
    try {
      const layRes  = await fetch(API_BASE_URL + '/api/favs-run');
      const layJson = await layRes.json();
      if (layJson.success) setLayData(layJson);
    } catch (_) {}
  };

  const formatRaceTime = rt => {
    if (!rt) return { date: '', time: '' };
    const m = rt.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})/);
    if (m) {
      const d = new Date(`${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}T${m[4].padStart(2,'0')}:${m[5]}:00Z`);
      return {
        date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', timeZone:'Europe/Dublin' }),
        time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Europe/Dublin' }),
      };
    }
    try {
      const d = new Date(rt.endsWith('Z') || rt.includes('+') ? rt : rt + 'Z');
      const tz = { timeZone: 'Europe/Dublin' };
      return {
        date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', ...tz }),
        time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12: false, ...tz }),
      };
    } catch { return { date: rt.substring(0,10), time: rt.substring(11,16) }; }
  };

  const formatDroppedMeta = pick => {
    const rawDropTs = pick?.dropped_at || pick?.drop_time || pick?.updated_at;
    let droppedAt = '--:--';
    if (rawDropTs) {
      try {
        const parsed = new Date(rawDropTs);
        if (!isNaN(parsed.getTime())) {
          droppedAt = parsed.toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Europe/Dublin',
          });
        }
      } catch {}
    }
    const reason = (pick?.drop_reason || pick?.removal_reason || pick?.drop_note || '').toString().trim();
    return {
      droppedAt,
      reason: reason || 'Live re-analysis pulled this selection',
    };
  };

  const outcomeStyle = emoji => {
    if (emoji === 'REMOVED') return { bg:'#6b7280', border:'#9ca3af', text:'REMOVED', card:'rgba(107,114,128,0.08)' };
    if (emoji === 'WIN')     return { bg:'#059669', border:'#10b981', text:'WIN \u2713',     card:'rgba(16,185,129,0.08)' };
    if (emoji === 'PLACED')  return { bg:'#3b82f6', border:'#60a5fa', text:'PLACED',          card:'rgba(59,130,246,0.08)' };
    if (emoji === 'LOSS')    return { bg:'#ef4444', border:'#f87171', text:'LOSS \u2715',     card:'rgba(239,68,68,0.06)'  };
    return                          { bg:'#6b7280', border:'#9ca3af', text:'PENDING \u23F3',  card:'rgba(107,114,128,0.06)' };
  };

  const scoreLabel = s => {
    const n = parseFloat(s || 0);
    if (n >= 95) return { bg:'#d97706', label:'ELITE'  };
    if (n >= 90) return { bg:'#059669', label:'STRONG' };
    if (n >= 80) return { bg:'#3b82f6', label:'GOOD'   };
    return             { bg:'#8b5cf6', label:'VALUE'  };
  };

  const getPostLossReview = pick => {
    const whySelected = (pick?.post_loss_why_selected || '').toString().trim();
    const whatMissed = (pick?.post_loss_what_missed || '').toString().trim();
    const howFix = (pick?.post_loss_how_fix || '').toString().trim();
    if (!whySelected && !whatMissed && !howFix) return null;
    return { whySelected, whatMissed, howFix };
  };

  const renderLossReviewPanel = (pick, compact = false) => {
    const review = getPostLossReview(pick);
    if (!review) return null;

    return (
      <div style={{
        marginTop:'8px',
        padding: compact ? '10px 11px' : '11px 14px',
        background:'rgba(249,115,22,0.08)',
        border:'1px solid rgba(249,115,22,0.28)',
        borderRadius:'9px'
      }}>
        <div style={{ fontSize: compact ? '10px' : '11px', fontWeight:'800', color:'#fdba74', textTransform:'uppercase', letterSpacing:'0.8px', marginBottom:'7px' }}>
          AI Post-Loss Review
        </div>
        {review.whySelected && (
          <div style={{ fontSize: compact ? '11px' : '12px', color:'rgba(255,255,255,0.78)', lineHeight:1.45, marginBottom: review.whatMissed || review.howFix ? '6px' : 0 }}>
            <strong style={{ color:'#fef3c7' }}>Why selected:</strong> {review.whySelected}
          </div>
        )}
        {review.whatMissed && (
          <div style={{ fontSize: compact ? '11px' : '12px', color:'rgba(255,255,255,0.78)', lineHeight:1.45, marginBottom: review.howFix ? '6px' : 0 }}>
            <strong style={{ color:'#fca5a5' }}>What missed:</strong> {review.whatMissed}
          </div>
        )}
        {review.howFix && (
          <div style={{ fontSize: compact ? '11px' : '12px', color:'rgba(255,255,255,0.78)', lineHeight:1.45 }}>
            <strong style={{ color:'#86efac' }}>How fix:</strong> {review.howFix}
          </div>
        )}
      </div>
    );
  };


  const dateRangeLabel = () => {
    const today = new Date();
    const yest  = new Date(); yest.setDate(yest.getDate() - 1);
    const fmt = d => d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short' });
    return `${fmt(yest)} – ${fmt(today)}`;
  };

  if (isFreeUser) return (
    <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'12px', padding:'40px 24px', textAlign:'center', color:'rgba(255,255,255,0.75)' }}>
      <div style={{ fontSize:'24px', marginBottom:'10px' }}>🔒</div>
      <div style={{ fontSize:'20px', fontWeight:'800', color:'white', marginBottom:'8px' }}>Latest Results is Premium-only</div>
      <div style={{ fontSize:'14px', opacity:0.85 }}>Upgrade to Premium or VIP to view the full latest-results dashboard.</div>
    </div>
  );

  if (loading) return (
    <div style={{ textAlign:'center', padding:'60px 20px', color:'white' }}>
      <div style={{ fontSize:'18px', opacity:0.8 }}>Loading latest results...</div>
    </div>
  );

  if (error) return (
    <div style={{ background:'rgba(239,68,68,0.15)', border:'1px solid #ef4444', borderRadius:'10px', padding:'24px', color:'white', textAlign:'center' }}>
      <div style={{ fontWeight:'700', marginBottom:'6px' }}>Error loading results</div>
      <div style={{ fontSize:'13px', opacity:0.8, marginBottom:'16px' }}>{error}</div>
      <button onClick={loadResults} style={{ background:'#059669', border:'none', borderRadius:'6px', color:'white', padding:'8px 20px', cursor:'pointer', fontWeight:'700' }}>Retry</button>
    </div>
  );

  const picks   = results?.picks   || [];
  const summary = results?.summary || {};
  const profit  = summary.profit   || 0;

  return (
    <div>
      {/* Header */}
      <div style={{ background:'linear-gradient(135deg,#1e3a5f 0%,#1e40af 50%,#1e3a5f 100%)', border:'2px solid #3b82f6', borderRadius:'12px', padding: isMobile ? '16px 14px' : '24px 28px', marginBottom:'24px', color:'white', display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'12px' }}>
        <div>
          <div style={{ fontSize:'13px', textTransform:'uppercase', letterSpacing:'1px', color:'#93c5fd', opacity:0.9 }}>Post-Race Analysis</div>
          <div style={{ fontSize:'22px', fontWeight:'800', marginTop:'4px' }}>Latest Results</div>
          <div style={{ fontSize:'13px', opacity:0.75, marginTop:'4px' }}>{dateRangeLabel()}</div>
        </div>
        <button onClick={loadResults} style={{ background:'rgba(255,255,255,0.15)', border:'1px solid rgba(255,255,255,0.4)', borderRadius:'8px', color:'white', padding:'8px 18px', cursor:'pointer', fontSize:'13px', fontWeight:'600' }}>
          Refresh
        </button>
      </div>

      {/* Summary bar */}
      {picks.length > 0 && (() => {
        const statsLeft = [
          { label:'Picks',  value: summary.total_picks || 0, color:'#93c5fd', bg:'rgba(96,165,250,0.12)', border:'rgba(96,165,250,0.3)',  icon:'🎯' },
          { label:'Won',    value: summary.wins || 0,        color:'#34d399', bg:'rgba(16,185,129,0.15)', border:'rgba(16,185,129,0.4)',  icon:'✅' },
          { label:'Placed', value: summary.places || 0,      color:'#818cf8', bg:'rgba(99,102,241,0.15)', border:'rgba(99,102,241,0.35)', icon:'🥈' },
          { label:'Lost',   value: summary.losses || 0,      color:'#f87171', bg:'rgba(239,68,68,0.13)',  border:'rgba(239,68,68,0.35)',  icon:'❌' },
          { label:'Removed', value: summary.removed || 0,    color:'#d1d5db', bg:'rgba(156,163,175,0.12)', border:'rgba(156,163,175,0.3)', icon:'⚠️' },
        ];
        const pnlPos       = profit >= 0;
        const cumulRoiVal  = cumulRoi?.success ? (cumulRoi.roi ?? 0) : null;
        const cumulSettled = cumulRoi?.success ? (cumulRoi.settled || 0) : null;
        return (
          <div style={{ marginBottom:'24px' }}>
            {/* Top row: 4 count stats */}
            <div style={{ display:'grid', gridTemplateColumns: isMobile ? 'repeat(2,1fr)' : 'repeat(5,1fr)', gap: isMobile ? '6px' : '10px', marginBottom:'10px' }}>
              {statsLeft.map((stat, i) => (
                <div key={i} style={{ background:stat.bg, border:`1.5px solid ${stat.border}`, borderRadius:'10px', padding: isMobile ? '10px 4px 8px' : '16px 10px 12px', textAlign:'center' }}>
                  <div style={{ fontSize: isMobile ? '14px' : '12px', marginBottom:'2px' }}>{stat.icon}</div>
                  <div style={{ fontSize: isMobile ? '20px' : '28px', fontWeight:'900', color:stat.color, lineHeight:1 }}>{stat.value}</div>
                  <div style={{ fontSize: isMobile ? '9px' : '11px', color:'rgba(255,255,255,0.55)', marginTop: isMobile ? '3px' : '5px', textTransform:'uppercase', letterSpacing: isMobile ? '0.5px' : '1px', fontWeight:'600' }}>{stat.label}</div>
                </div>
              ))}
            </div>
            {/* Bottom row: ROI spanning full width */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr', gap:'10px' }}>
              <div style={{
                background: cumulRoiVal === null
                  ? 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(99,102,241,0.05))'
                  : cumulRoiVal >= 0
                    ? 'linear-gradient(135deg, rgba(5,150,105,0.25) 0%, rgba(16,185,129,0.12) 50%, rgba(4,120,87,0.2) 100%)'
                    : 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(185,28,28,0.1))',
                border: `2px solid ${cumulRoiVal === null ? 'rgba(99,102,241,0.3)' : cumulRoiVal >= 0 ? 'rgba(52,211,153,0.5)' : 'rgba(239,68,68,0.4)'}`,
                borderRadius:'16px',
                padding: isMobile ? '20px 16px' : '28px 32px',
                boxShadow: cumulRoiVal >= 0
                  ? '0 0 40px rgba(52,211,153,0.15), 0 0 80px rgba(52,211,153,0.05), inset 0 1px 0 rgba(255,255,255,0.05)'
                  : '0 4px 20px rgba(0,0,0,0.2)',
                position: 'relative',
                overflow: 'hidden',
              }}>
                {/* Subtle shine overlay */}
                <div style={{ position:'absolute', top:0, left:0, right:0, height:'1px', background:'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)' }} />
                <div style={{ display:'flex', flexDirection: isMobile ? 'column' : 'row', alignItems:'center', gap: isMobile ? '20px' : '0' }}>
                  {/* Left: emoji + ROI */}
                  <div style={{ flex:1, display:'flex', alignItems: isMobile ? 'center' : 'flex-start', gap: isMobile ? '16px' : '20px', flexDirection: isMobile ? 'column' : 'row', textAlign: isMobile ? 'center' : 'left' }}>
                    <div style={{ fontSize: isMobile ? '36px' : '48px', lineHeight:1, filter:'drop-shadow(0 2px 8px rgba(0,0,0,0.3))' }}>💰</div>
                    <div>
                      <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.5)', textTransform:'uppercase', letterSpacing:'1.5px', fontWeight:'700', marginBottom:'6px' }}>Return on Investment</div>
                      <div style={{
                        fontSize: isMobile ? '38px' : '56px',
                        fontWeight:'900',
                        color: cumulRoiVal === null ? '#818cf8' : cumulRoiVal >= 0 ? '#34d399' : '#f87171',
                        lineHeight:1,
                        textShadow: cumulRoiVal >= 0 ? '0 0 30px rgba(52,211,153,0.4), 0 0 60px rgba(52,211,153,0.15)' : 'none',
                        letterSpacing:'-1px',
                      }}>
                        {cumulRoiVal === null ? '—' : `${cumulRoiVal >= 0 ? '+' : ''}${cumulRoiVal.toFixed(1)}%`}
                      </div>
                      <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.45)', marginTop:'8px', fontWeight:'500' }}>
                        {cumulRoiVal === null ? 'Loading…' : `Since 22 Mar · ${cumulSettled} settled`}
                      </div>
                    </div>
                  </div>
                  {/* Right: impact stat + download */}
                  <div style={{ display:'flex', flexDirection:'column', alignItems: isMobile ? 'center' : 'flex-end', gap:'14px' }}>
                    {cumulRoiVal !== null && (
                      <div style={{
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '12px',
                        padding: isMobile ? '12px 20px' : '14px 24px',
                        textAlign: 'center',
                        maxWidth: '260px',
                      }}>
                        <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.7)', lineHeight:'1.5' }}>
                          Across all bets, every <span style={{ color:'white', fontWeight:'800' }}>€1</span> staked returned
                          <span style={{ color: cumulRoiVal >= 0 ? '#34d399' : '#f87171', fontWeight:'800', fontSize:'15px' }}> €{(1 + cumulRoiVal / 100).toFixed(2)}</span> on average
                          — a {cumulRoiVal >= 0 ? 'profit' : 'loss'} of <span style={{ color: cumulRoiVal >= 0 ? '#34d399' : '#f87171', fontWeight:'800' }}>€{Math.abs(cumulRoiVal / 100).toFixed(2)}</span> per bet
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => {
                        const btn = document.getElementById('csv-download-btn');
                        if (btn) btn.textContent = '⏳ Downloading...';
                        fetch(API_BASE_URL + '/api/results/export-csv')
                          .then(r => r.text())
                          .then(csv => {
                            const blob = new Blob([csv], { type: 'text/csv' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url; a.download = 'BetBudAI_ROI_Data.csv'; a.click();
                            URL.revokeObjectURL(url);
                            if (btn) btn.textContent = '✅ Downloaded!';
                            setTimeout(() => { if (btn) btn.textContent = '📥 Download CSV'; }, 3000);
                          })
                          .catch(() => { if (btn) btn.textContent = '❌ Failed'; setTimeout(() => { if (btn) btn.textContent = '📥 Download CSV'; }, 3000); });
                      }}
                      id="csv-download-btn"
                      style={{ padding:'10px 20px', background:'linear-gradient(135deg,#3b82f6,#2563eb)', color:'white', border:'none', borderRadius:'8px', fontSize:'13px', fontWeight:'700', cursor:'pointer', boxShadow:'0 3px 10px rgba(37,99,235,0.3)', transition:'all 0.2s', letterSpacing:'0.3px', whiteSpace:'nowrap' }}
                    >📥 Download CSV</button>
                    <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.35)', textAlign:'center', maxWidth:'160px', lineHeight:'1.3' }}>Every pick logged pre-race · fully transparent</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── PERFORMANCE DASHBOARD ────────────────────────────────────── */}
      {false && cumulRoi?.success && (() => {
        const cr         = cumulRoi;
        const roi        = cr.roi ?? 0;
        const roiPos     = roi >= 0;
        const byDay      = cr.by_day || [];
        const maxAbsProfit = byDay.length > 0 ? Math.max(...byDay.map(d => Math.abs(d.profit)), 0.1) : 1;
        const avgWinSc   = cr.avg_win_score;
        const avgLossSc  = cr.avg_loss_score;
        const scoregap   = (avgWinSc && avgLossSc) ? (avgWinSc - avgLossSc).toFixed(1) : null;
        const winSR      = cr.settled > 0 ? Math.round(cr.wins / cr.settled * 100) : 0;
        const wpSR       = cr.settled > 0 ? Math.round((cr.wins + cr.places) / cr.settled * 100) : 0;
        let runningStake = 0; let runningRet = 0;
        const byDayWithRoi = byDay.map(d => {
          runningStake += d.settled;
          runningRet   += (d.settled + d.profit);
          const rRoi = runningStake > 0 ? ((runningRet - runningStake) / runningStake * 100) : 0;
          return { ...d, runningRoi: Math.round(rRoi * 10) / 10 };
        });
        return (
          <div style={{ marginBottom:'20px', background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'12px', padding:'16px 18px' }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'14px', flexWrap:'wrap', gap:'8px' }}>
              <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.4)', fontWeight:'700' }}>📊 Performance Dashboard</div>
              <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.3)' }}>Since {cr.start_date} · {cr.settled} settled</div>
            </div>

            {/* 4 stat tiles */}
            <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap:'8px', marginBottom:'14px' }}>
              <div style={{ background: roiPos ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.1)', border:`1.5px solid ${roiPos ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.3)'}`, borderRadius:'10px', padding:'12px 14px' }}>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', textTransform:'uppercase', letterSpacing:'0.8px', fontWeight:'600', marginBottom:'4px' }}>Return on Investment</div>
                <div style={{ fontSize:'26px', fontWeight:'900', color: roiPos ? '#34d399' : '#f87171', lineHeight:1 }}>{roiPos ? '+' : ''}{roi.toFixed(1)}%</div>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.35)', marginTop:'5px', lineHeight:1.5 }}>£{cr.total_return?.toFixed(2)} returned<br/>on £{cr.total_stake?.toFixed(0)} staked</div>
              </div>
              <div style={{ background: cr.profit >= 0 ? 'rgba(16,185,129,0.10)' : 'rgba(239,68,68,0.08)', border:`1.5px solid ${cr.profit >= 0 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.25)'}`, borderRadius:'10px', padding:'12px 14px' }}>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', textTransform:'uppercase', letterSpacing:'0.8px', fontWeight:'600', marginBottom:'4px' }}>Profit</div>
                <div style={{ fontSize:'26px', fontWeight:'900', color: cr.profit >= 0 ? '#34d399' : '#f87171', lineHeight:1 }}>{cr.profit >= 0 ? '+' : ''}{cr.profit?.toFixed(2)}u</div>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.35)', marginTop:'5px', lineHeight:1.5 }}>{cr.wins}W · {cr.places}P · {cr.losses}L<br/>{cr.pending > 0 ? `${cr.pending} pending` : 'all settled'}</div>
              </div>
              <div style={{ background:'rgba(96,165,250,0.08)', border:'1.5px solid rgba(96,165,250,0.25)', borderRadius:'10px', padding:'12px 14px' }}>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', textTransform:'uppercase', letterSpacing:'0.8px', fontWeight:'600', marginBottom:'4px' }}>Win Rate</div>
                <div style={{ fontSize:'26px', fontWeight:'900', color: winSR >= 25 ? '#34d399' : '#fbbf24', lineHeight:1 }}>{winSR}%</div>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.35)', marginTop:'5px', lineHeight:1.5 }}>Win+Place: {wpSR}%<br/>{cr.wins} wins from {cr.settled}</div>
              </div>
              <div style={{ background:'rgba(139,92,246,0.08)', border:'1.5px solid rgba(139,92,246,0.25)', borderRadius:'10px', padding:'12px 14px' }}>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', textTransform:'uppercase', letterSpacing:'0.8px', fontWeight:'600', marginBottom:'4px' }}>Model Signal</div>
                <div style={{ fontSize:'26px', fontWeight:'900', color: scoregap >= 15 ? '#34d399' : scoregap >= 8 ? '#fbbf24' : '#f87171', lineHeight:1 }}>{scoregap ? `+${scoregap}` : '—'}</div>
                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.35)', marginTop:'5px', lineHeight:1.5 }}>Winner avg: {avgWinSc ?? '—'}<br/>Loser avg: {avgLossSc ?? '—'}</div>
              </div>
            </div>

            {/* ROI formula explainer */}
            <div style={{ background:'rgba(59,130,246,0.07)', border:'1px solid rgba(59,130,246,0.18)', borderRadius:'8px', padding:'9px 13px', marginBottom:'14px', fontSize:'11px', color:'rgba(255,255,255,0.45)', lineHeight:1.6 }}>
              <span style={{ color:'rgba(255,255,255,0.7)', fontWeight:'700' }}>How Return on Investment is calculated: </span>
              Level-stakes method — 1 unit wagered per pick (industry-standard tipster measure).
              Wins return stake × decimal odds. Place returns ½ stake at ¼ odds. Loss forfeits stake.
              <span style={{ color:'rgba(255,255,255,0.55)', display:'block', marginTop:'2px' }}>
                Return on Investment = (total returned − total staked) ÷ total staked × 100
              </span>
            </div>

            {/* Day-by-day bar chart */}
            {byDay.length > 0 && (
              <div>
                <div style={{ fontSize:'10px', textTransform:'uppercase', letterSpacing:'0.8px', color:'rgba(255,255,255,0.3)', fontWeight:'700', marginBottom:'8px' }}>Daily breakdown</div>
                <div style={{ display:'flex', flexDirection:'column', gap:'5px' }}>
                  {[...byDayWithRoi].reverse().map((d, i) => {
                    const pos  = d.profit >= 0;
                    const barW = Math.round(Math.abs(d.profit) / maxAbsProfit * 100);
                    const dt   = new Date(d.date + 'T12:00:00');
                    const dow  = dt.toLocaleDateString('en-GB', { weekday:'short' });
                    const dom  = dt.toLocaleDateString('en-GB', { day:'numeric', month:'short' });
                    const isSat = dt.getDay() === 6;
                    const isSun = dt.getDay() === 0;
                    return (
                      <div key={i} style={{ display:'grid', gridTemplateColumns: isMobile ? '62px 1fr 46px' : '88px 1fr 56px', gap:'8px', alignItems:'center' }}>
                        <div style={{ fontSize:'11px', color: isSat ? '#f97316' : isSun ? '#38bdf8' : 'rgba(255,255,255,0.55)', fontWeight: (isSat||isSun) ? '700' : '400', lineHeight:1.3 }}>
                          <span style={{ fontWeight:'700' }}>{dow}</span> {dom}
                          <div style={{ fontSize:'9px', color:'rgba(255,255,255,0.3)', marginTop:'1px' }}>{d.wins}W {d.places}P {d.losses}L</div>
                        </div>
                        <div style={{ position:'relative', height:'20px', background:'rgba(255,255,255,0.05)', borderRadius:'4px', overflow:'hidden' }}>
                          <div style={{ position:'absolute', top:0, bottom:0, left:0, width:`${barW}%`, background: pos ? 'rgba(16,185,129,0.5)' : 'rgba(239,68,68,0.45)', borderRadius:'4px' }}/>
                          <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', paddingLeft:'7px', fontSize:'10px', color:'rgba(255,255,255,0.7)', fontWeight:'600' }}>
                            {pos ? '+' : ''}{d.profit.toFixed(2)}u
                          </div>
                        </div>
                        <div style={{ fontSize:'10px', color: d.runningRoi >= 0 ? '#34d399' : '#f87171', fontWeight:'700', textAlign:'right' }}>
                          {d.runningRoi >= 0 ? '+' : ''}{d.runningRoi}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Win summary headline */}
      {picks.length > 0 && (() => {
        const settled = (summary.wins || 0) + (summary.losses || 0) + (summary.places || 0);
        const winPct  = settled > 0 ? Math.round((summary.wins || 0) / settled * 100) : 0;
        const isGood  = winPct >= 33;
        return (
          <div style={{ background: isGood ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.10)', border:`1px solid ${isGood ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.3)'}`, borderRadius:'10px', padding: isMobile ? '10px 14px' : '13px 22px', marginBottom:'20px', textAlign:'center', color:'white', fontSize: isMobile ? '14px' : '17px', fontWeight:'700', letterSpacing:'0.2px', lineHeight:1.4 }}>
            {summary.wins || 0} win{(summary.wins || 0) !== 1 ? 's' : ''} from {settled} settled &mdash; {winPct}% strike rate
            {(summary.pending || 0) > 0 && (
              <div style={{ fontSize: isMobile ? '11px' : '13px', color:'rgba(255,255,255,0.55)', fontWeight:'500', marginTop: isMobile ? '3px' : '0', display: isMobile ? 'block' : 'inline' }}>
                {isMobile ? '' : <span style={{marginLeft:'12px'}} />}({summary.pending} still pending)
              </div>
            )}
          </div>
        );
      })()}

      {/* Saturday / Sunday pattern panel — removed 2026-03-30 */}
      {false && picks.length > 0 && (() => {
        // Group settled picks by day-of-week, tracking scores + market-leader alignment
        const DOW_STATS = {};
        picks.forEach(p => {
          const rt = p.race_time;
          if (!rt) return;
          let d;
          try {
            const m = rt.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})/);
            d = m ? new Date(`${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}`) : new Date(rt);
          } catch { return; }
          const dow = d.toLocaleDateString('en-GB', { weekday:'long' });
          if (!DOW_STATS[dow]) DOW_STATS[dow] = {
            wins:0, places:0, losses:0, pending:0, picks:0,
            winScores:[], lossScores:[], mlCount:0, oddsAbove5:0
          };
          DOW_STATS[dow].picks++;
          const oc  = (p.result_emoji || p.outcome || '').toUpperCase();
          const sc  = parseFloat(p.comprehensive_score || p.analysis_score || 0);
          const sb  = p.score_breakdown || {};
          const ml  = parseFloat(sb.market_leader || 0) > 0;
          const odd = parseFloat(p.odds || 0);
          if (ml) DOW_STATS[dow].mlCount++;
          if (odd >= 5) DOW_STATS[dow].oddsAbove5++;
          if (oc === 'WIN' || oc === 'WON')        { DOW_STATS[dow].wins++;   if(sc) DOW_STATS[dow].winScores.push(sc); }
          else if (oc === 'PLACED')                { DOW_STATS[dow].places++; if(sc) DOW_STATS[dow].lossScores.push(sc); }
          else if (oc === 'LOSS' || oc === 'LOST') { DOW_STATS[dow].losses++; if(sc) DOW_STATS[dow].lossScores.push(sc); }
          else                                       DOW_STATS[dow].pending++;
        });
        const hasSat = DOW_STATS['Saturday'];
        const hasSun = DOW_STATS['Sunday'];
        if (!hasSat && !hasSun) return null;

        const avg = arr => arr.length ? Math.round(arr.reduce((a,b)=>a+b,0)/arr.length*10)/10 : null;

        const dayCard = (dow, st, emoji, col) => {
          const settled = st.wins + st.losses + st.places;
          const sr        = settled > 0 ? Math.round(st.wins / settled * 100) : null;
          const avgWin    = avg(st.winScores);
          const avgLoss   = avg(st.lossScores);
          const gap       = (avgWin && avgLoss) ? Math.round((avgWin - avgLoss)*10)/10 : null;
          const mlPct     = st.picks > 0 ? Math.round(st.mlCount / st.picks * 100) : null;
          const longPct   = settled > 0 ? Math.round(st.oddsAbove5 / settled * 100) : null;
          return (
            <div key={dow} style={{ flex:1, minWidth: isMobile ? '100%' : 0, background:'rgba(255,255,255,0.04)', border:`1px solid ${col}33`, borderRadius:'10px', padding:'14px 16px', borderLeft:`4px solid ${col}` }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'10px' }}>
                <div style={{ fontSize:'13px', fontWeight:'800', color:col }}>{emoji} {dow}</div>
                {sr !== null && (
                  <span style={{ background: sr >= 30 ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.15)', color: sr >= 30 ? '#34d399' : '#f87171', borderRadius:'5px', padding:'2px 8px', fontWeight:'800', fontSize:'13px' }}>
                    {sr}% win rate
                  </span>
                )}
              </div>
              {/* W / P / L row */}
              <div style={{ display:'flex', gap:'8px', fontSize:'13px', marginBottom:'10px' }}>
                <span style={{ color:'#34d399', fontWeight:'700' }}>{st.wins}W</span>
                <span style={{ color:'#818cf8', fontWeight:'700' }}>{st.places}P</span>
                <span style={{ color:'#f87171', fontWeight:'700' }}>{st.losses}L</span>
                {st.pending > 0 && <span style={{ color:'rgba(255,255,255,0.35)', fontSize:'12px' }}>{st.pending} pending</span>}
              </div>
              {/* Stats grid */}
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'6px 12px', fontSize:'11px' }}>
                {avgWin!=null && (
                  <div style={{ color:'rgba(255,255,255,0.5)' }}>
                    Avg winner score
                    <div style={{ color:'#34d399', fontWeight:'800', fontSize:'13px' }}>{avgWin}</div>
                  </div>
                )}
                {avgLoss!=null && (
                  <div style={{ color:'rgba(255,255,255,0.5)' }}>
                    Avg loser score
                    <div style={{ color:'#f87171', fontWeight:'800', fontSize:'13px' }}>{avgLoss}</div>
                  </div>
                )}
                {gap!=null && (
                  <div style={{ color:'rgba(255,255,255,0.5)' }}>
                    Model discrimination
                    <div style={{ color: gap >= 15 ? '#34d399' : gap >= 8 ? '#fbbf24' : '#f87171', fontWeight:'800', fontSize:'13px' }}>
                      {gap > 0 ? '+' : ''}{gap} pts gap
                    </div>
                  </div>
                )}
                {mlPct!=null && (
                  <div style={{ color:'rgba(255,255,255,0.5)' }}>
                    Market leader picks
                    <div style={{ color: mlPct >= 35 ? '#34d399' : '#fbbf24', fontWeight:'800', fontSize:'13px' }}>{mlPct}%</div>
                  </div>
                )}
              </div>
            </div>
          );
        };

        const satSt = hasSat || { wins:0, places:0, losses:0, pending:0, picks:0, winScores:[], lossScores:[], mlCount:0, oddsAbove5:0 };
        const sunSt = hasSun || { wins:0, places:0, losses:0, pending:0, picks:0, winScores:[], lossScores:[], mlCount:0, oddsAbove5:0 };
        const satSettled = satSt.wins + satSt.losses + satSt.places;
        const sunSettled = sunSt.wins + sunSt.losses + sunSt.places;
        const showExplainer = hasSat && hasSun && satSettled > 0 && sunSettled > 0 &&
          (sunSt.wins / Math.max(sunSettled,1)) > (satSt.wins / Math.max(satSettled,1));

        const satGap   = (avg(satSt.winScores) && avg(satSt.lossScores)) ? (avg(satSt.winScores) - avg(satSt.lossScores)).toFixed(1) : null;
        const sunGap   = (avg(sunSt.winScores) && avg(sunSt.lossScores)) ? (avg(sunSt.winScores) - avg(sunSt.lossScores)).toFixed(1) : null;
        const satML    = satSt.picks > 0 ? Math.round(satSt.mlCount / satSt.picks * 100) : null;
        const sunML    = sunSt.picks > 0 ? Math.round(sunSt.mlCount / sunSt.picks * 100) : null;

        return (
          <div style={{ marginBottom:'20px', background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.09)', borderRadius:'10px', padding:'14px 18px' }}>
            <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.4)', marginBottom:'12px', fontWeight:'700' }}>
              📅 Weekend Day Breakdown
            </div>
            <div style={{ display:'flex', gap:'10px', flexWrap:'wrap', marginBottom: showExplainer ? '14px' : 0 }}>
              {hasSat && dayCard('Saturday', satSt, '🏆', '#f97316')}
              {hasSun && dayCard('Sunday',   sunSt, '☀️', '#38bdf8')}
            </div>

            {showExplainer && (
              <div style={{ display:'flex', flexDirection:'column', gap:'8px' }}>

                {/* Headline insight: score discrimination */}
                {satGap && sunGap && (
                  <div style={{ background:'rgba(59,130,246,0.1)', border:'1px solid rgba(59,130,246,0.3)', borderRadius:'8px', padding:'10px 14px' }}>
                    <div style={{ fontSize:'11px', fontWeight:'800', color:'#60a5fa', marginBottom:'8px' }}>🔬 Why the Model Performs Better on Sundays — Data Evidence</div>
                    <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap:'8px', marginBottom:'8px' }}>
                      <div style={{ background:'rgba(249,115,22,0.1)', borderRadius:'6px', padding:'8px 10px', borderLeft:'3px solid #f97316' }}>
                        <div style={{ fontSize:'11px', color:'#fb923c', fontWeight:'700', marginBottom:'4px' }}>Saturday — narrow gap</div>
                        <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.6)', lineHeight:1.5 }}>
                          Avg winner score: <b style={{color:'#34d399'}}>{avg(satSt.winScores)}</b><br/>
                          Avg loser score:  <b style={{color:'#f87171'}}>{avg(satSt.lossScores)}</b><br/>
                          <span style={{ color:'#fbbf24', fontWeight:'800' }}>Separation: only {satGap} pts</span><br/>
                          <span style={{ color:'rgba(255,255,255,0.45)', fontSize:'11px' }}>Model can barely tell winners from losers</span>
                        </div>
                      </div>
                      <div style={{ background:'rgba(56,189,248,0.1)', borderRadius:'6px', padding:'8px 10px', borderLeft:'3px solid #38bdf8' }}>
                        <div style={{ fontSize:'11px', color:'#38bdf8', fontWeight:'700', marginBottom:'4px' }}>Sunday — clear gap</div>
                        <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.6)', lineHeight:1.5 }}>
                          Avg winner score: <b style={{color:'#34d399'}}>{avg(sunSt.winScores)}</b><br/>
                          Avg loser score:  <b style={{color:'#f87171'}}>{avg(sunSt.lossScores)}</b><br/>
                          <span style={{ color:'#34d399', fontWeight:'800' }}>Separation: {sunGap} pts</span><br/>
                          <span style={{ color:'rgba(255,255,255,0.45)', fontSize:'11px' }}>Winning picks clearly stand out</span>
                        </div>
                      </div>
                    </div>
                    <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.5)', lineHeight:1.55 }}>
                      When the winner is only a few points ahead of the losers in our scoring model, it means the race conditions are too noisy for the model to edge out a reliable selection. Sunday cards produce a cleaner signal.
                    </div>
                  </div>
                )}

                {/* 4 structural reasons */}
                <div style={{ background:'rgba(249,115,22,0.07)', border:'1px solid rgba(249,115,22,0.22)', borderRadius:'8px', padding:'10px 14px' }}>
                  <div style={{ fontSize:'11px', fontWeight:'800', color:'#fb923c', marginBottom:'8px' }}>⚡ Why Saturdays are structurally harder</div>
                  <div style={{ display:'flex', flexDirection:'column', gap:'7px', fontSize:'12px', color:'rgba(255,255,255,0.55)', lineHeight:1.55 }}>
                    <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                      <span style={{ fontSize:'13px', flexShrink:0 }}>🎯</span>
                      <div><b style={{color:'rgba(255,255,255,0.8)'}}>Hyper-efficient markets.</b> Saturday showpiece meetings (Lincoln, Curragh, Kempton features) attract 5–10× more Betfair liquidity than Sunday cards. Prices get hammered close to true probability, leaving no exploitable edge for a form-based model.</div>
                    </div>
                    <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                      <span style={{ fontSize:'13px', flexShrink:0 }}>📋</span>
                      <div><b style={{color:'rgba(255,255,255,0.8)'}}>Season-openers &amp; raiders missing from database.</b> Big Saturday cards regularly feature horses returning from winter breaks (no recent UK form) and Irish cross-channel raiders. Our model scores them near-zero for database history — then they go and win.</div>
                    </div>
                    <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                      <span style={{ fontSize:'13px', flexShrink:0 }}>🎲</span>
                      <div><b style={{color:'rgba(255,255,255,0.8)'}}>Bigger, more chaotic fields.</b> Heritage handicaps (Lincoln 21 runners, Spring Cup 16+ runners) are deliberately designed to be competitive. Draw bias, pace scenarios and traffic in running override form signals — the model has no visibility of these factors.</div>
                    </div>
                    <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                      <span style={{ fontSize:'13px', flexShrink:0 }}>☀️</span>
                      <div><b style={{color:'rgba(255,255,255,0.8)'}}>Sunday = smaller fields, complete form records.</b> Provincial meetings (Naas, Carlisle, Stratford) run 6–10 runner fields where every horse has a full UK/Irish form profile, tighter odds and less chaos. The model's signals — consistency, going suitability, meeting focus — discriminate cleanly and {satML!=null && sunML!=null ? `our Sunday picks align with market opinion ${sunML}% of the time vs ${satML}% on Saturdays` : 'our picks align with the market far more often'}.
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        );
      })()}

      {picks.length === 0 ? (
        <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'12px', padding:'48px 24px', textAlign:'center', color:'rgba(255,255,255,0.7)' }}>
          <div style={{ fontSize:'18px', fontWeight:'700', color:'white', marginBottom:'8px' }}>No picks found for today or yesterday</div>
          <div style={{ fontSize:'14px' }}>Today's and yesterday's AI selections will appear here once picks have been generated and results recorded.</div>
        </div>
      ) : (
        <div style={{ background:'rgba(255,255,255,0.05)', borderRadius:'14px', overflow:'hidden', border:'1px solid rgba(255,255,255,0.12)' }}>
          {/* Table header — desktop only */}
          {!isMobile && (
          <div style={{ display:'grid', gridTemplateColumns:'90px 55px 110px 1fr 70px minmax(0,2fr) 80px', gap:'0', background:'rgba(30,58,95,0.9)', padding:'10px 16px', fontSize:'11px', fontWeight:'800', color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'0.8px', alignItems:'center' }}>
            <span>Result</span>
            <span>Day</span>
            <span>Time / Course</span>
            <span>Horse</span>
            <span style={{textAlign:'center'}}>Rating</span>
            <span>Key Reason</span>
            <span style={{textAlign:'center'}}>Odds</span>
          </div>
          )}
          {(() => {
            const layMap = {};
            (layData?.races || []).forEach(r => {
              if (!r.outcome) return;
              const rt = r.race_time || '';
              const hhmm = rt.length >= 16 ? rt.substring(11, 16) : '';
              const course = (r.course || '').toLowerCase();
              if (hhmm && course) layMap[`${course}|${hhmm}`] = r.outcome;
            });
          return [...picks].sort((a, b) => {
            const ta = a.race_time || ''; const tb = b.race_time || '';
            // ISO strings sort lexicographically; US format needs normalising
            const norm = s => { const m = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})/); return m ? `${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}T${m[4].padStart(2,'0')}:${m[5]}` : s; };
            return norm(tb).localeCompare(norm(ta));
          }).map((pick, idx) => {
            // Derive display emoji: normalise emoji/string/lowercase outcome variants
            const rawOutcome = (() => {
              if (pick.is_dropped) return 'REMOVED';
              const re = pick.result_emoji || '';
              const oc = (pick.outcome || '').toLowerCase();
              if (re === '\u2705' || oc === 'win' || oc === 'won')    return 'WIN';
              if (re === '\uD83D\uDD35' || oc === 'placed')           return 'PLACED';
              if (re === '\u274C' || oc === 'loss' || oc === 'lost')  return 'LOSS';
              return null;
            })();
            const oc    = outcomeStyle(rawOutcome);
            const tier  = scoreLabel(pick.comprehensive_score || pick.analysis_score);
            const ft    = formatRaceTime(pick.race_time);
            const score = parseFloat(pick.comprehensive_score || pick.analysis_score || 0);
            const winner = pick.result_winner_name || pick.winner_name;
            const pnl   = parseFloat(pick.profit || 0);
            const dropMeta = formatDroppedMeta(pick);
            const isRemoved = rawOutcome === 'REMOVED';
            const isPending = !rawOutcome || rawOutcome === 'PENDING';
            const displayOdds = !isPending && pick.sp_odds ? parseFloat(pick.sp_odds) : parseFloat(pick.odds || 0);
            // Key reason: only show result_analysis for settled picks (no pre-race breakdown for free users)
            const keyReason = isRemoved ? `Dropped at ${dropMeta.droppedAt} • ${dropMeta.reason}` : (!isPending && pick.result_analysis ? pick.result_analysis : '');
            const winnerNote = !isPending && !isRemoved && winner && winner !== pick.horse ? `Winner: ${winner}` : '';
            const lossReviewPanel = rawOutcome === 'LOSS' ? renderLossReviewPanel(pick, isMobile) : null;
            // Fav outcome from lay analysis
            const layOutcome = (() => {
              const hhmm = ft.time;
              const course = (pick.course || pick.race_course || '').toLowerCase();
              if (!hhmm || !course) return null;
              return layMap[`${course}|${hhmm}`] || null;
            })();
            const layFavWon = layOutcome && ['win','won','loss','lost'].includes(layOutcome.toLowerCase()) ? ['win','won'].includes(layOutcome.toLowerCase()) : null;

            if (isMobile) return (
              /* ── Mobile card layout ── */
              <div key={idx} style={{ padding:'12px 14px', borderBottom:'1px solid rgba(255,255,255,0.08)', background: idx % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent', borderLeft:`3px solid ${oc.border}` }}>
                {/* Row 1: result + horse + P&L */}
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'8px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'8px', flex:1, minWidth:0 }}>
                    <span style={{ flexShrink:0, display:'inline-block', background:oc.bg, color:'white', padding:'3px 7px', borderRadius:'5px', fontSize:'10px', fontWeight:'800' }}>
                      {isPending ? '⏳' : oc.text}
                    </span>
                    <div style={{ minWidth:0 }}>
                      <div style={{ fontWeight:'800', color:'white', fontSize:'14px', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{pick.horse || '—'}</div>
                      <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'1px' }}>
                        {ft.time}{ft.time && pick.course ? ' · ' : ''}{pick.course || ''}
                        {score > 0 && <span style={{ marginLeft:'6px', background:tier.bg, color:'white', padding:'1px 6px', borderRadius:'4px', fontSize:'10px', fontWeight:'700' }}>{score.toFixed(0)} {tier.label}</span>}
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign:'right', flexShrink:0 }}>
                    <div style={{ fontSize:'13px', color:'#93c5fd', fontWeight:'700' }}>{displayOdds > 1 ? toFractional(displayOdds) : ''}</div>
                  </div>
                </div>
                {/* Row 2: key reason + winner note — no truncation on mobile */}
                {(keyReason || winnerNote) && (
                  <div style={{ marginTop:'5px', fontSize:'11px', lineHeight:1.4 }}>
                    {keyReason && <span style={{ color:'rgba(255,255,255,0.5)' }}>{keyReason}</span>}
                    {winnerNote && <div style={{ color:'#f87171', marginTop:'2px' }}>{winnerNote}</div>}
                  </div>
                )}
                {lossReviewPanel}
                {!isRemoved && layFavWon !== null && (
                  <div style={{ marginTop:'4px' }}>
                    <span style={{ background: layFavWon ? 'rgba(248,113,113,0.18)' : 'rgba(52,211,153,0.18)', color: layFavWon ? '#f87171' : '#34d399', border:`1px solid ${layFavWon ? 'rgba(248,113,113,0.5)' : 'rgba(52,211,153,0.5)'}`, borderRadius:'4px', padding:'2px 8px', fontSize:'10px', fontWeight:'800' }}>
                      {layFavWon ? '✗ FAV WON' : '✓ FAV LOST'}
                    </span>
                  </div>
                )}
              </div>
            );

            return (
              <div key={idx} style={{ borderBottom:'1px solid rgba(255,255,255,0.07)', background: idx % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent', borderLeft:`3px solid ${oc.border}` }}>
                {/* ── Desktop table row ── */}
                <div style={{ display:'grid', gridTemplateColumns:'90px 55px 110px 1fr 70px minmax(0,2fr) 80px', gap:'0', padding:'11px 16px', alignItems:'center' }}>
                  {/* Result badge */}
                  <span style={{ display:'inline-block', background:oc.bg, color:'white', padding:'4px 8px', borderRadius:'6px', fontSize:'11px', fontWeight:'800', letterSpacing:'0.3px', textAlign:'center', width:'fit-content' }}>
                    {isPending ? '⏳ PENDING' : oc.text}
                  </span>

                  {/* Day */}
                  <span style={{ background: pick._dayLabel === 'Today' ? '#7c3aed' : '#374151', color:'white', padding:'3px 7px', borderRadius:'5px', fontSize:'10px', fontWeight:'800', textTransform:'uppercase', textAlign:'center', width:'fit-content' }}>
                    {pick._dayLabel === 'Today' ? 'Today' : 'Yest'}
                  </span>

                  {/* Time + Course */}
                  <div style={{ lineHeight:1.3 }}>
                    <div style={{ fontWeight:'700', color:'white', fontSize:'13px' }}>{ft.time || '—'}</div>
                    <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.5)', marginTop:'1px' }}>{pick.course || ''}</div>
                  </div>

                  {/* Horse */}
                  <div style={{ fontWeight:'800', color:'white', fontSize:'14px', paddingRight:'8px' }}>
                    {pick.horse || '—'}
                    {pick.trainer && <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', fontWeight:'400', marginTop:'1px' }}>{pick.trainer}</div>}
                  </div>

                  {/* Rating */}
                  <div style={{ textAlign:'center' }}>
                    {score > 0 && (
                      <span style={{ background:tier.bg, color:'white', padding:'3px 7px', borderRadius:'5px', fontSize:'11px', fontWeight:'800', display:'block', textAlign:'center' }}>
                        {score.toFixed(0)}
                      </span>
                    )}
                    {score > 0 && <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.4)', marginTop:'2px', textAlign:'center' }}>{tier.label}</div>}
                  </div>

                  {/* Key reason + winner note + fav outcome */}
                  <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.6)', paddingRight:'8px', lineHeight:1.4 }}>
                    {keyReason && <span>{keyReason}</span>}
                    {winnerNote && <div style={{ fontSize:'11px', color:'#f87171', marginTop:'2px' }}>{winnerNote}</div>}
                    {!isRemoved && layFavWon !== null && (
                      <div style={{ marginTop:'6px' }}>
                        <span style={{ background: layFavWon ? 'rgba(248,113,113,0.18)' : 'rgba(52,211,153,0.18)', color: layFavWon ? '#f87171' : '#34d399', border:`1px solid ${layFavWon ? 'rgba(248,113,113,0.5)' : 'rgba(52,211,153,0.5)'}`, borderRadius:'4px', padding:'2px 8px', fontSize:'10px', fontWeight:'800' }}>
                          {layFavWon ? '✗ FAV WON' : '✓ FAV LOST'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Odds / P&L */}
                  <div style={{ textAlign:'center' }}>
                    <div style={{ fontSize:'13px', fontWeight:'700', color:'#93c5fd' }}>{displayOdds > 1 ? toFractional(displayOdds) : '—'}</div>
                    {Number.isFinite(pnl) && !isPending && !isRemoved && (
                      <div style={{ fontSize:'11px', color:pnl >= 0 ? '#34d399' : '#f87171', fontWeight:'800', marginTop:'2px' }}>{pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}u</div>
                    )}
                  </div>
                </div>
                {lossReviewPanel && (
                  <div style={{ padding:'0 16px 12px 16px' }}>
                    {lossReviewPanel}
                  </div>
                )}
              </div>
            );
          });
          })()}
        </div>

      )}

      {/* ── Loss / Placed Analysis ─ moved to Admin page ─────── */}

      <div style={{ marginTop:'16px', padding:'14px 18px', background:'rgba(255,255,255,0.06)', borderRadius:'10px', color:'rgba(255,255,255,0.45)', fontSize:'12px', textAlign:'center', lineHeight:'1.6' }}>
        Results are recorded after each race. Pending picks update as results come in. · Always bet responsibly.
      </div>
      <LegalDisclaimerCard />
    </div>
  );
}
// ---- Major Races ----
const PUNCHESTOWN_RACECARD_META = {
  date: new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' }),
  course: 'Punchestown',
  broadcaster: 'Racing TV',
  going: 'Yielding',
  surface: 'Turf',
  sourceLabel: 'Sporting Life racecards',
  sourceUrl: 'https://www.sportinglife.com/racing/racecards',
};

const PUNCHESTOWN_RACECARD = [
  {
    time: '14:30',
    title: 'Specialist Group Novice Hurdle',
    details: '4YO plus, 11 runners, 2m 90y',
    analysis: {
      going: 'Yielding',
      surface: 'Turf',
      status: 'Weighed In',
      offTime: '14:30',
      winningTime: '4m 5.70s',
    },
    runners: [
      {
        horse: 'Colcannon',
        jockey: 'Donagh Meyler',
        odds: '5/2',
        officialRating: '125',
        analysis: 'Smart bumper performer who belatedly built on the promise of his hurdling debut when winning 25-runner maiden at Fairyhouse (2m, soft) earlier in the month, leading on bridle before 2 out. Will need to improve again to take this but that\'s possible.',
        tags: ['D'],
      },
      { horse: 'Fort Dino', jockey: "Mike O'Connor" },
      { horse: 'Friary Road', jockey: "Shane O'Callaghan (5)" },
      { horse: 'Gameball', jockey: "Darragh O'Keeffe" },
      { horse: "Leader D'allier", jockey: 'Paul Townend' },
      { horse: "Nadia's Boy", jockey: "Sean O'Keeffe" },
      { horse: 'Ionian', jockey: 'N de Boinville' },
      { horse: 'Techno Davis', jockey: 'J J Slevin' },
      { horse: 'Beauvallon', jockey: 'Danny Mullins' },
      { horse: 'Immediate Effect', jockey: 'Jack Kennedy' },
      { horse: 'Alwaysgoinhome', jockey: 'Shane Fitzgerald' },
    ],
  },
  {
    time: '15:05',
    title: 'Close Brothers Irish EBF Mares Novice Hurdle (Listed)',
    details: '4YO plus, 5 runners, Class 1, 2m 90y',
    runners: [
      { horse: 'Catchabird', jockey: 'Aidan Kelly' },
      { horse: 'Alliteration', jockey: 'Keith Donoghue' },
      { horse: 'Diamond Du Berlais', jockey: 'Mr P W Mullins' },
      { horse: 'Future Prospect', jockey: 'Paul Townend' },
      { horse: 'Adrienne', jockey: "Darragh O'Keeffe" },
    ],
  },
  {
    time: '15:40',
    title: 'Mongey Communications La Touche Cup Cross Country Chase',
    details: '5YO plus, 13 runners, 4m 1f 11y',
    runners: [
      { horse: 'Outside The Door', jockey: 'Aidan Kelly (3)' },
      { horse: 'Busselton', jockey: "Darragh O'Keeffe" },
      { horse: 'Desertmore House', jockey: 'Ricky Doyle' },
      { horse: 'Dorans Law', jockey: 'Mr B J Walsh (7)' },
      { horse: 'Shannon Royale', jockey: 'Keith Donoghue' },
      { horse: 'Vital Island', jockey: 'Mr B T Stone (7)' },
      { horse: 'Benny The Duke', jockey: 'Mr F P Murphy (7)' },
      { horse: 'Bodhisattva', jockey: 'Alex Harvey' },
      { horse: 'Cavalry Master', jockey: "Sean O'Keeffe" },
      { horse: 'Lough Derg Spirit', jockey: 'Mr J J Berry (7)' },
      { horse: 'The Bosses Oscar', jockey: 'Miss G Benson (7)' },
      { horse: 'The Goffer', jockey: 'Jack Kennedy' },
      { horse: 'Walking On Glass', jockey: 'Peter Smithers (7)' },
    ],
  },
  {
    time: '16:15',
    title: 'Conway Piling Handicap Hurdle (Listed)',
    details: '4YO plus, 24 runners, Class 1, 2m 7f 110y',
    runners: [
      { horse: 'Hewick', jockey: 'Paddy Hanlon (5)' },
      { horse: 'Karl Des Tourelles', jockey: 'Brian Hayes' },
      { horse: 'Da Capo Glory', jockey: 'Michael Kenneally (5)' },
      { horse: 'Minella Sixo', jockey: 'Jack Kennedy' },
      { horse: 'The Big Clubman', jockey: "Sean O'Keeffe" },
      { horse: 'Champagne Chic', jockey: 'Lorcan Williams' },
      { horse: 'Duke Silver', jockey: 'Hugh Horgan (5)' },
      { horse: "Grann's Boy", jockey: "Darragh O'Keeffe" },
      { horse: 'Onewaywest', jockey: 'Ben Jones' },
      { horse: 'Daydream Nation', jockey: 'Ben Harvey' },
      { horse: 'Ballybow', jockey: 'Danny Gilligan' },
      { horse: 'Ballystone', jockey: 'Alex Harvey' },
      { horse: 'Ballykinlar', jockey: 'Shane Fenelon (5)' },
      { horse: 'Fillyoureye', jockey: 'Danny Mullins' },
      { horse: 'Blue Mosque', jockey: 'Donagh Meyler' },
      { horse: "Margaret's Legacy", jockey: 'Harry Bannister' },
      { horse: 'Seaniecon', jockey: "Jonjo O'Neill Jr." },
      { horse: 'Fad Eadrainn', jockey: 'Simon Torrens' },
      { horse: 'Icare Desbois', jockey: 'Cian Quirke' },
      { horse: 'Sign From Above', jockey: 'Sam Ewing' },
      { horse: 'The Lovely Man', jockey: 'Conor Stone-Walsh' },
      { horse: 'Billy Lee Swagger', jockey: "Shane O'Callaghan (5)" },
      { horse: "Bridie's Beau", jockey: "Patrick M O'Brien (5)" },
      { horse: 'Chance Another One', jockey: 'Daniel King' },
    ],
  },
  {
    time: '16:50',
    title: 'Frontline Security Handicap Chase (Listed)',
    details: '5YO plus, 20 runners, Class 1, 2m 75y',
    runners: [
      { horse: 'Ballysax Hank', jockey: 'James Bowen' },
      { horse: 'Western Diego', jockey: 'Brian Hayes' },
      { horse: 'Come Walk With Me', jockey: 'Donagh Meyler' },
      { horse: 'Coral River', jockey: 'Sean Flanagan' },
      { horse: 'Escapeandevade', jockey: "Paul O'Brien" },
      { horse: 'Raffles Dolce Vita', jockey: 'J J Slevin' },
      { horse: "Path D'oroux", jockey: 'Ben Harvey' },
      { horse: 'Release The Beast', jockey: 'Eoin Staples (5)' },
      { horse: 'The King Of Prs', jockey: 'Keith Donoghue' },
      { horse: 'Relieved Of Duties', jockey: 'Jack Kennedy' },
      { horse: 'Sky Lord', jockey: "Darragh O'Keeffe" },
      { horse: 'Birdie Or Bust', jockey: 'H Cobden' },
      { horse: 'Golden Joy', jockey: 'Danny Gilligan' },
      { horse: 'Indiana Jones', jockey: "Shane O'Callaghan (5)" },
      { horse: 'Jalila Moriviere', jockey: 'Simon Torrens' },
      { horse: 'McLaurey', jockey: 'Mark Walsh' },
      { horse: 'Petit Tonnerre', jockey: 'R P McLernon' },
      { horse: 'Seskin Flash', jockey: 'Conor Stone-Walsh' },
      { horse: 'Dont Go Yet', jockey: 'Sarah Kavanagh (7)' },
      { horse: 'Tuckmill', jockey: 'J J Burke' },
    ],
  },
  {
    time: '17:25',
    title: 'Barberstown Castle Novice Chase (Grade 1)',
    details: '5YO plus, 5 runners, Class 1, 2m 75y',
    runners: [
      { horse: 'Irish Panther', jockey: 'Kieren Buckley' },
      { horse: "Jacob's Ladder", jockey: 'Jack Kennedy' },
      { horse: 'Kopek Des Bordes', jockey: 'Paul Townend' },
      { horse: 'Pure Steel', jockey: 'Mark Walsh' },
      { horse: 'Salvator Mundi', jockey: 'H Cobden' },
    ],
  },
  {
    time: '18:05',
    title: 'Ladbrokes Champion Stayers Hurdle (Grade 1)',
    details: '4YO plus, 8 runners, Class 1, 2m 7f 110y',
    runners: [
      { horse: 'Bob Olinger', jockey: "Darragh O'Keeffe" },
      { horse: 'Franciscan Rock', jockey: 'Josh Williamson' },
      { horse: 'Honesty Policy', jockey: 'H Cobden' },
      { horse: 'Jimmy Du Seuil', jockey: 'Paul Townend' },
      { horse: 'Kawaboomga', jockey: 'Mark Walsh' },
      { horse: 'Meet And Greet', jockey: 'Phillip Enright' },
      { horse: 'Teahupoo', jockey: 'Jack Kennedy' },
      { horse: 'Jetara', jockey: 'Sam Ewing' },
    ],
  },
  {
    time: '18:35',
    title: 'JP & M Doyle (C & G) Flat Race',
    details: '4YO to 7YO, 10 runners, 2m 90y',
    runners: [
      { horse: "Bois D'angos", jockey: 'Mr F R Buckley (7)' },
      { horse: 'Bon Bon Fizz', jockey: 'Mr J M Halford (7)' },
      { horse: 'Outofafrika', jockey: 'Mr D G Lavery' },
      { horse: 'Soul Asylum', jockey: 'Mr H C Swan' },
      { horse: 'Cowboy Casanova', jockey: "Mr D O'Connor" },
      { horse: 'Highlander Addict', jockey: 'Mr D Doyle (7)' },
      { horse: "It's Good To Talk", jockey: 'Mr J L Gleeson' },
      { horse: 'Adaboy Mushy', jockey: 'Mr B T Stone (7)' },
      { horse: 'Our Trigger', jockey: 'Miss J Townend' },
      { horse: 'Quiryn', jockey: 'Mr P W Mullins' },
    ],
  },
];

const PUNCHESTOWN_RUNNER_DETAILS = {
  Colcannon: { trainer: 'N Meade', age: '6', weight: '11-12' },
  'Fort Dino': { trainer: 'H De Bromhead', age: '5', weight: '11-12' },
  'Friary Road': { trainer: 'T M Walsh', age: '6', weight: '11-12' },
  Gameball: { trainer: 'H De Bromhead', age: '6', weight: '11-12' },
  "Leader D'allier": { trainer: 'W P Mullins', age: '5', weight: '11-12' },
  "Nadia's Boy": { trainer: 'W P Mullins', age: '6', weight: '11-12' },
  Ionian: { trainer: 'N J Henderson', age: '5', weight: '11-5' },
  'Techno Davis': { trainer: "J P O'Brien", age: '5', weight: '11-5' },
  Beauvallon: { trainer: 'W P Mullins', age: '4', weight: '11-4' },
  'Immediate Effect': { trainer: 'G Elliott', age: '4', weight: '11-4' },
  Alwaysgoinhome: { trainer: 'B Cawley', age: '4', weight: '10-11' },

  Catchabird: { trainer: 'Ms S J Connell', age: '8', weight: '11-7' },
  Alliteration: { trainer: 'J P Dempsey', age: '5', weight: '11-4' },
  'Diamond Du Berlais': { trainer: 'W P Mullins', age: '5', weight: '11-4' },
  'Future Prospect': { trainer: 'W P Mullins', age: '6', weight: '11-4' },
  Adrienne: { trainer: 'T M Walsh', age: '4', weight: '10-10' },

  'Outside The Door': { trainer: 'P Roche', age: '10', weight: '12-3' },
  Busselton: { trainer: 'E Bolger', age: '9', weight: '11-12' },
  'Desertmore House': { trainer: 'M Brassil', age: '11', weight: '11-12' },
  'Dorans Law': { trainer: 'P J Rothwell', age: '8', weight: '11-12' },
  'Shannon Royale': { trainer: 'Ian Donoghue', age: '8', weight: '11-12' },
  'Vital Island': { trainer: "R P O'Keeffe", age: '14', weight: '11-12' },
  'Benny The Duke': { trainer: 'Brendan Walsh', age: '9', weight: '11-7' },
  Bodhisattva: { trainer: 'J C McConnell', age: '9', weight: '11-7' },
  'Cavalry Master': { trainer: 'P Maher', age: '12', weight: '11-7' },
  'Lough Derg Spirit': { trainer: 'D P Murphy', age: '14', weight: '11-7' },
  'The Bosses Oscar': { trainer: 'N Slevin', age: '11', weight: '11-7' },
  'The Goffer': { trainer: 'G Elliott', age: '9', weight: '11-7' },
  'Walking On Glass': { trainer: 'P Roche', age: '11', weight: '11-7' },

  Hewick: { trainer: 'J J Hanlon', age: '11', weight: '12-0' },
  'Karl Des Tourelles': { trainer: 'P Fenton', age: '6', weight: '11-4' },
  'Da Capo Glory': { trainer: 'Padraig Butler', age: '9', weight: '10-13' },
  'Minella Sixo': { trainer: 'G Elliott', age: '7', weight: '10-13' },
  'The Big Clubman': { trainer: 'P Nolan', age: '6', weight: '10-13' },
  'Champagne Chic': { trainer: 'J Scott', age: '6', weight: '10-11' },
  'Duke Silver': { trainer: "J P O'Brien", age: '6', weight: '10-11' },
  "Grann's Boy": { trainer: 'H Rogers', age: '6', weight: '10-11' },
  Onewaywest: { trainer: 'B Pauling', age: '7', weight: '10-10' },
  'Daydream Nation': { trainer: 'William Harvey', age: '6', weight: '10-9' },
  Ballybow: { trainer: 'G Elliott', age: '7', weight: '10-8' },
  Ballystone: { trainer: 'J C McConnell', age: '8', weight: '10-8' },
  Ballykinlar: { trainer: 'M Bowen', age: '7', weight: '10-7' },
  Fillyoureye: { trainer: 'W P Mullins', age: '6', weight: '10-6' },
  'Blue Mosque': { trainer: 'N Meade', age: '6', weight: '10-5' },
  "Margaret's Legacy": { trainer: 'W Greatrex', age: '9', weight: '10-5' },
  Seaniecon: { trainer: "J & A O'Neill", age: '5', weight: '10-5' },
  'Fad Eadrainn': { trainer: 'P T Foley', age: '8', weight: '10-4' },
  'Icare Desbois': { trainer: 'D H Kelly', age: '8', weight: '10-3' },
  'Sign From Above': { trainer: 'Peter Fahey', age: '8', weight: '10-3' },
  'The Lovely Man': { trainer: 'G P Cromwell', age: '7', weight: '10-3' },
  'Billy Lee Swagger': { trainer: 'P J Rothwell', age: '7', weight: '10-0' },
  "Bridie's Beau": { trainer: 'G P Cromwell', age: '7', weight: '10-0' },
  'Chance Another One': { trainer: 'E Mullins', age: '7', weight: '10-0' },

  'Ballysax Hank': { trainer: 'G P Cromwell', age: '7', weight: '11-12' },
  'Western Diego': { trainer: 'W P Mullins', age: '9', weight: '11-11' },
  'Come Walk With Me': { trainer: 'E Cawley', age: '7', weight: '11-10' },
  'Coral River': { trainer: "R O'Sullivan", age: '7', weight: '11-7' },
  Escapeandevade: { trainer: 'Harry Derham', age: '10', weight: '11-7' },
  'Raffles Dolce Vita': { trainer: 'T Gibney', age: '5', weight: '11-7' },
  "Path D'oroux": { trainer: 'G P Cromwell', age: '9', weight: '11-6' },
  'Release The Beast': { trainer: 'P Nolan', age: '7', weight: '11-6' },
  'The King Of Prs': { trainer: 'G P Cromwell', age: '8', weight: '11-6' },
  'Relieved Of Duties': { trainer: 'G Elliott', age: '7', weight: '11-5' },
  'Sky Lord': { trainer: 'H De Bromhead', age: '7', weight: '11-5' },
  'Birdie Or Bust': { trainer: 'H De Bromhead', age: '8', weight: '11-4' },
  'Golden Joy': { trainer: 'G Elliott', age: '7', weight: '11-4' },
  'Indiana Jones': { trainer: 'M F Morris', age: '10', weight: '11-4' },
  'Jalila Moriviere': { trainer: 'W P Mullins', age: '7', weight: '11-4' },
  McLaurey: { trainer: 'E Mullins', age: '7', weight: '11-4' },
  'Petit Tonnerre': { trainer: "J & A O'Neill", age: '8', weight: '11-2' },
  'Seskin Flash': { trainer: 'J P Dempsey', age: '7', weight: '10-9' },
  'Dont Go Yet': { trainer: 'E Cawley', age: '12', weight: '10-3' },
  Tuckmill: { trainer: 'Peter Fahey', age: '10', weight: '10-0' },

  'Irish Panther': { trainer: 'E & P Harty', age: '9', weight: '11-12' },
  "Jacob's Ladder": { trainer: 'G Elliott', age: '7', weight: '11-12' },
  'Kopek Des Bordes': { trainer: 'W P Mullins', age: '6', weight: '11-12' },
  'Pure Steel': { trainer: 'J J Mangan', age: '6', weight: '11-12' },
  'Salvator Mundi': { trainer: 'W P Mullins', age: '6', weight: '11-12' },

  'Bob Olinger': { trainer: 'H De Bromhead', age: '11', weight: '11-10' },
  'Franciscan Rock': { trainer: 'M F Morris', age: '9', weight: '11-10' },
  'Honesty Policy': { trainer: 'G Elliott', age: '6', weight: '11-10' },
  'Jimmy Du Seuil': { trainer: 'W P Mullins', age: '7', weight: '11-10' },
  Kawaboomga: { trainer: 'W P Mullins', age: '6', weight: '11-10' },
  'Meet And Greet': { trainer: 'O McKiernan', age: '10', weight: '11-10' },
  Teahupoo: { trainer: 'G Elliott', age: '9', weight: '11-10' },
  Jetara: { trainer: 'Mrs J Harrington', age: '8', weight: '11-3' },

  "Bois D'angos": { trainer: 'J C McConnell', age: '6', weight: '12-0' },
  'Bon Bon Fizz': { trainer: 'G Elliott', age: '6', weight: '12-0' },
  Outofafrika: { trainer: 'G P Cromwell', age: '5', weight: '12-0' },
  'Soul Asylum': { trainer: 'G Elliott', age: '5', weight: '12-0' },
  'Cowboy Casanova': { trainer: 'M Bowen', age: '5', weight: '11-7' },
  'Highlander Addict': { trainer: 'P J Flynn', age: '5', weight: '11-7' },
  "It's Good To Talk": { trainer: 'E Mullins', age: '5', weight: '11-7' },
  'Adaboy Mushy': { trainer: 'D Queally', age: '4', weight: '11-6' },
  'Our Trigger': { trainer: 'W P Mullins', age: '4', weight: '11-6' },
  Quiryn: { trainer: 'W P Mullins', age: '4', weight: '11-6' },
};

const PUNCHESTOWN_RACE_ANALYSIS = {
  '14:30': { going: 'Yielding', surface: 'Turf', status: 'Weighed In', offTime: '14:30', winningTime: '4m 5.70s' },
  '15:05': { going: 'Yielding', surface: 'Turf', status: 'Weighed In', offTime: '15:05', winningTime: '4m 13.20s' },
  '15:40': {
    going: 'Good to Yielding (Yielding in places)',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '15:40',
    winningTime: '9m 11.40s',
    fullResult: '1) Jetbob (IRE) 28/1 | 2) Hearts And Spades (FR) 4/5 f | 3) Squire Ohara (IRE) 12/1',
  },
  '16:15': {
    going: 'Yielding',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '16:16',
    winningTime: '6m 2.30s',
    fullResult: '1) Wonderwall (IRE) 9/2 | 2) Its On The Line (IRE) 5/2 f',
  },
  '16:50': {
    going: 'Yielding',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '16:50',
    winningTime: '4m 7.30s',
    fullResult: '1) Dinoblue (FR) 2/5 f | 2) Spindleberry (IRE) 9/2',
  },
  '17:25': {
    going: 'Yielding',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '17:25',
    winningTime: '4m 8.80s',
    fullResult: '1) Funiculi Funicula (FR) 7/2 | 2) Norn Iron (IRE) 12/1 | 3) Spread Boss Ted 14/1',
  },
  '18:00': {
    going: 'Yielding',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '18:00',
    winningTime: '6m 2.30s',
    fullResult: '1) King Rasko Grey (FR) 8/13 f | 2) Lord Byron (IRE) 7/1 | 3) Kiely\'s Place (IRE) 10/1',
  },
  '18:40': {
    going: 'Yielding',
    surface: 'Turf',
    status: 'Weighed In',
    offTime: '18:40',
    winningTime: '4m 10.70s',
    fullResult: '1) Lossiemouth (FR) 2/7 f | 2) Golden Ace 11/1',
  },
};

const PUNCHESTOWN_RUNNER_ANALYSIS = {
  'Colcannon': { info: 'Age: 6| Weight: 11-12| J: Donagh Meyler| T: N Meade| OR: 125| D', odds: '5/2', verdict: 'Smart bumper performer who belatedly built on the promise of his hurdling debut when winning 25-runner maiden at Fairyhouse (2m, soft) earlier in the month, leading on bridle before 2 out. Will need to improve again to take this but that\'s possible.' },
  'Fort Dino': { info: 'Age: 5| Weight: 11-12| J: Mike O\'Connor| T: H De Bromhead', odds: '22/1', verdict: 'Only fourth at Dieppe on debut but showed plenty of improvement despite making a fairly serious error at the fourth when winning 11-runner juvenile at Auteuil (17f, soft) when last seen 11 months ago. Has since left Hugo Merienne and should progress again (tongue tied here).' },
  'Friary Road': { info: 'Age: 6| Weight: 11-12| J: Shane O\'Callaghan(5)| T: T M Walsh| OR: 120| CD', odds: '40/1', verdict: 'Made a winning hurdling debut at Navan last September but has failed to complete on both subsequent starts, keeping on from a poor position when coming down at the last on handicap debut here (17f, soft) in November. Needs to get back on track.' },
  'Gameball': { info: 'Age: 6| Weight: 11-12| J: Darragh O\'Keeffe| T: H De Bromhead| OR: 133| CD', odds: '5/1', verdict: 'Bumper winner for Andy Slattery in July and followed up on Punchestown hurdle debut for this yard 12 weeks later. Took a step forward up in grade when fourth of 8 in Royal Bond Novices\' Hurdle at Fairyhouse (2m, soft) in November and should have more to offer. Hood applied.' },
  "Leader D'allier": { info: 'Age: 5| Weight: 11-12| J: Paul Townend| T: W P Mullins| BF| CD', odds: '3/1', verdict: 'Multiple bumper winner in France for Mathieu Pitart and built on promising yard/hurdling debut effort when easily landing the odds here in January. Proved a major let-down even so stepping up in class when tailed off in Hardy Eustace Novices\' Hurdle at Fairyhouse recently so bounce back needed.' },
  "Nadia's Boy": { info: 'Age: 6| Weight: 11-12| J: Sean O\'Keeffe| T: W P Mullins| D', odds: '6/1', verdict: 'Successful on sole outing in points and also made a winning start under Rules in Kilbeggan bumper last summer. Maintained unbeaten record sent hurdling in 11-runner maiden at Listowel back in September and with that form franked since, he\'s a major player with further progress likely.' },
  'Ionian': { info: 'Age: 5| Weight: 11-5| J: N de Boinville| T: N J Henderson| OR: 114', odds: '10/1', verdict: 'Has been placed twice from 4 starts in this sphere, giving it a good shot from the front when third in a 10-runner Warwick novice (2m, good to soft) 8 weeks ago. English raider who will need to up his game pitched against some useful prospects from W. P. Mullins.' },
  'Techno Davis': { info: 'Age: 5| Weight: 11-5| J: J J Slevin| T: J P O\'Brien', odds: '10/1', verdict: 'EUR160,000 3-y-o, No Risk At All gelding. Half-brother to fair hurdler Disco Davis, stays 2.5m. Won sole start in points (Mar 21) and will be interesting to see what the market makes of him on debut for his in-form handler.' },
  'Beauvallon': { info: 'Age: 4| Weight: 11-4| J: Danny Mullins| T: W P Mullins| D', odds: '28/1', verdict: 'Fair maiden on Flat in France who left his hurdling debut form behind in recording a first career success in 11-runner juvenile at Limerick (2m, soft, 6/4) last month, his jumping in need of polish. Will go on improving as he gains experience.' },
  'Immediate Effect': { info: 'Age: 4| Weight: 11-4| J: Jack Kennedy| T: G Elliott| OR: 128| BF| CD', odds: '14/1', verdict: 'Useful Flat winner for Sir Mark Prescott and made a winning start over hurdles for new yard in maiden over C&D on New Year\'s Eve. Found Grade 1 at Leopardstown too demanding next time and can probably have his latest effort in listed company overlooked.' },
  'Alwaysgoinhome': { info: 'Age: 4| Weight: 10-11| J: Shane Fitzgerald| T: B Cawley', odds: '300/1', verdict: 'Dawn Approach gelding. Dam bumper winner. Best watched on debut.' },

  'Catchabird': { info: 'Age: 8| Weight: 11-7| J: Aidan Kelly| T: Ms S J Connell| OR: 109| D', odds: '28/1', verdict: 'Landed 2m Wexford maiden before following up in 12-runner handicap at Navan (2m, soft) 40 days ago. This is a tough ask, though.' },
  'Alliteration': { info: 'Age: 5| Weight: 11-4| J: Keith Donoghue| T: J P Dempsey| OR: 117| D', odds: '10/1', verdict: 'Improving sort who was fitted with cheekpieces and a tongue strap when landing 2m Fairyhouse maiden recently. Thriving but this demands a clear personal best.' },
  'Diamond Du Berlais': { info: 'Age: 5| Weight: 11-4| J: Mr P W Mullins| T: W P Mullins| OR: 132', odds: '7/4', verdict: 'Useful ex-French hurdler. Made a winning start for current yard at Ludlow in February and backed it up with a very good sixth of 22 to White Noise in Dawn Run at Cheltenham (17f, good) 49 days ago. The clear form pick.' },
  'Future Prospect': { info: 'Age: 6| Weight: 11-4| J: Paul Townend| T: W P Mullins| OR: 129| D', odds: '10/11', verdict: 'Useful bumper winner who made a winning start over hurdles in 2m Naas maiden in January. Good fourth of 11 in Grade 1 at Fairyhouse last time so she\'s a likely player.' },
  'Adrienne': { info: 'Age: 4| Weight: 10-10| J: Darragh O\'Keeffe| T: T M Walsh| OR: 122| D', odds: '15/2', verdict: 'Scored at Fairyhouse in November and back on track with fourth of 9 in Percy Maynard Juvenile Hurdle at Fairyhouse (2m, soft) 24 days ago. No forlorn hope.' },

  'Outside The Door': { info: 'Age: 10| Weight: 12-3| J: Aidan Kelly(3)| T: P Roche| OR: 137| C', odds: '14/1', verdict: 'Career-best effort when winning handicap chase at Wexford last summer. However, ran poorly next 2 starts and fared no better switched to this discipline when well beaten in race won by Desertmore House here in November.' },
  'Busselton': { info: 'Age: 9| Weight: 11-12| J: Darragh O\'Keeffe| T: E Bolger| OR: 133| CD', odds: '7/2', verdict: 'Game winner of this race last year. Hasn\'t kicked on since, but after 4 months off (left Joseph Patrick O\'Brien) he faced an inadequate test over hurdles (2m) at Cork 25 days ago. Interesting with recent run behind him and blinkers reapplied.' },
  'Desertmore House': { info: 'Age: 11| Weight: 11-12| J: Ricky Doyle| T: M Brassil| OR: 138| C', odds: '13/8', verdict: 'Took well to this discipline when second in this race last year and, following a point success, scored comfortably back here in November. Well held at the Cheltenham Festival last time, but no surprise to see him bounce back at this venue.' },
  'Dorans Law': { info: 'Age: 8| Weight: 11-12| J: Mr B J Walsh(7)| T: P J Rothwell| OR: 113', odds: '28/1', verdict: 'Opened account over fences in a Wexford handicap last summer. After 6 months off, possibly needed the run when pulled up in the Ulster National at Downpatrick in March, though he has plenty to find making first start in this discipline.' },
  'Shannon Royale': { info: 'Age: 8| Weight: 11-12| J: Keith Donoghue| T: Ian Donoghue| OR: 128| C', odds: '11/2', verdict: 'Useful chaser at best for Gordon Elliott but yet to fire for current yard, down the field in first cross-country event here in February. Seemed to down tools before keeping on again late when fifth of 15 in Ulster National at Downpatrick last time.' },
  'Vital Island': { info: 'Age: 14| Weight: 11-12| J: Mr B T Stone(7)| T: R P O\'Keeffe| OR: 128| C', odds: '25/1', verdict: 'Veteran who recorded a third cross-country success at this Festival last year (landed the La Touche in 2023). However, pulled up next 2 starts before hampered when unseated rider at Cheltenham in December. Looks vulnerable to his younger rivals.' },
  'Benny The Duke': { info: 'Age: 9| Weight: 11-7| J: Mr F P Murphy(7)| T: Brendan Walsh', odds: '50/1', verdict: 'Hurdles winner but he\'s a maiden pointer and well beaten both starts over fences under Rules, finding it tough when seventh of 12 in this race last year when trained by Mark John Scallan.' },
  'Bodhisattva': { info: 'Age: 9| Weight: 11-7| J: Alex Harvey| T: J C McConnell| OR: 107', odds: '22/1', verdict: 'Losing run is mounting up, but with visor reapplied he ran better than for a while when fourth of 11 in handicap chase at Haydock 15 days ago. He\'s hard to catch right, though, and faces a tough ask (well beaten in this race in 2024).' },
  'Cavalry Master': { info: 'Age: 12| Weight: 11-7| J: Sean O\'Keeffe| T: P Maher| OR: 98| C', odds: '80/1', verdict: 'One-time useful chaser but form has gone the wrong way, including in cross-country events, pulled up in handicap chase at Fairyhouse on latest outing 26 days ago.' },
  'Lough Derg Spirit': { info: 'Age: 14| Weight: 11-7| J: Mr J J Berry(7)| T: D P Murphy| OR: 112', odds: '25/1', verdict: 'Third in the Foxhunter at Aintree for this yard back in 2023. Successful in points since but unseated early on cross-country debut here in November and pulled up in hunter chase at Gowran last month.' },
  'The Bosses Oscar': { info: 'Age: 11| Weight: 11-7| J: Miss G Benson(7)| T: N Slevin| OR: 138', odds: '50/1', verdict: 'Didn\'t manage to match his hurdling form sent chasing back in 2021/22. After a spell over hurdles, pulled up in hunter chase at Down Royal in December 2023 and hasn\'t been seen under Rules since (previously trained by Gordon Elliott).' },
  'The Goffer': { info: 'Age: 9| Weight: 11-7| J: Jack Kennedy| T: G Elliott| OR: 135| C', odds: '4/1', verdict: 'Hasn\'t won under Rules since November 2023 but runner-up twice in cross-country events here this season, beaten by Vanillier in February. In first-time cheekpieces, well held at Cheltenham last time and has stamina to prove over this longer distance.' },
  'Walking On Glass': { info: 'Age: 11| Weight: 11-7| J: Peter Smithers(7)| T: P Roche| OR: 125', odds: '28/1', verdict: 'Fairly useful chaser at best and fared better than for a while over jumps when third in handicap hurdle at this course last summer. However, making first start in this discipline he was tailed off here in November.' },

  'Hewick': { info: 'Age: 11| Weight: 12-0| J: Paddy Hanlon(5)| T: J J Hanlon| OR: 147| D', odds: '25/1', verdict: 'High-class chaser (winner of the 2023 King George at Kempton) and no slouch in this sphere either but evidence this season suggests his best days are behind him.' },
  'Karl Des Tourelles': { info: 'Age: 6| Weight: 11-4| J: Brian Hayes| T: P Fenton| OR: 137', odds: '13/2', verdict: 'Thirteen runs since his last win in 2024 but he ran a cracker back hurdling when sixth of 24 in the Martin Pipe at Cheltenham (2.5m) last month. Solid operator who deserves to land one of these.' },
  'Da Capo Glory': { info: 'Age: 9| Weight: 10-13| J: Michael Kenneally(5)| T: Padraig Butler| OR: 132| C', odds: '14/1', verdict: 'Course winner. 80/1, creditable eighth of 24 in Martin Pipe at Cheltenham (2.5m) 48 days ago. Good conditional booked and another bold show is likely.' },
  'Minella Sixo': { info: 'Age: 7| Weight: 10-13| J: Jack Kennedy| T: G Elliott| OR: 132| D', odds: '16/1', verdict: 'On a losing run but comes here in good nick, eleventh of 24 in Pertemps at Cheltenham (3m, good) 49 days ago.' },
  'The Big Clubman': { info: 'Age: 6| Weight: 10-13| J: Sean O\'Keeffe| T: P Nolan| OR: 132', odds: '16/1', verdict: 'Debut Wexford maiden winner. Useful form after and found drop back in trip against him when second of 6 in novice hurdle at Newbury (21f) in February. Cheekpieces go on for handicap hurdle debut and capable of better back over this longer trip.' },
  'Champagne Chic': { info: 'Age: 6| Weight: 10-11| J: Lorcan Williams| T: J Scott| OR: 130| D', odds: '14/1', verdict: 'A dual 3m winner at Wincanton and Haydock this year. Lost ground at start when a good twelfth of 24 in Pertemps at Cheltenham (3m, good) last time. Remains open to improvement and possibly the most interesting of the British challengers (won 2 of last 3 renewals).' },
  'Duke Silver': { info: 'Age: 6| Weight: 10-11| J: Hugh Horgan(5)| T: J P O\'Brien| OR: 130| D', odds: '14/1', verdict: 'Back to winning ways at Leopardstown in December and comes here in good nick, challenging wide when twelfth of 22 in handicap hurdle at Aintree (25f, good to soft) 19 days ago.' },
  "Grann's Boy": { info: 'Age: 6| Weight: 10-11| J: Darragh O\'Keeffe| T: H Rogers| OR: 130| BF', odds: '22/1', verdict: 'Latest win in hurdle at Listowel in September. Respectable sixth of 15 in handicap hurdle at Fairyhouse (21f, soft) 24 days ago. Cheekpieces go on for 1st time.' },
  'Onewaywest': { info: 'Age: 7| Weight: 10-10| J: Ben Jones| T: B Pauling| OR: 129', odds: '20/1', verdict: 'Scored at Warwick and Wetherby in November and not disgraced when fourteenth of 24 in Pertemps at Cheltenham (3m) 49 days ago.' },
  'Daydream Nation': { info: 'Age: 6| Weight: 10-9| J: Ben Harvey| T: William Harvey| OR: 128| D', odds: '11/1', verdict: 'Lightly-raced sort who bagged 10-runner handicap at Leopardstown (3m) in March. Very good third of 20 in handicap at Fairyhouse (3m) 26 days ago. Not out of things with cheekpieces added.' },
  'Ballybow': { info: 'Age: 7| Weight: 10-8| J: Danny Gilligan| T: G Elliott| OR: 127| D', odds: '40/1', verdict: 'Fairly useful hurdler at up to 3m but not yet at that level over fences this season. More is needed back in this sphere.' },
  'Ballystone': { info: 'Age: 8| Weight: 10-8| J: Alex Harvey| T: J C McConnell| OR: 127| D', odds: '50/1', verdict: 'Career best when winning 3m handicap hurdle at Galway 9 months ago. This is no easy comeback run, though.' },
  'Ballykinlar': { info: 'Age: 7| Weight: 10-7| J: Shane Fenelon(5)| T: M Bowen| OR: 126', odds: '16/1', verdict: 'A 3-time winner last summer for Donncha Duggan and has started well for new yard, seventh of 22 in handicap hurdle at Aintree (2.5m) 20 days ago.' },
  'Fillyoureye': { info: 'Age: 6| Weight: 10-6| J: Danny Mullins| T: W P Mullins| OR: 125| BF| CD', odds: '9/1', verdict: 'C&D winner in February but pulled up in handicap hurdle at Fairyhouse (3m) 26 days ago. Too free there and is worth another chance with few miles on the clock.' },
  'Blue Mosque': { info: 'Age: 6| Weight: 10-5| J: Donagh Meyler| T: N Meade| OR: 124', odds: '6/1', verdict: 'On a losing sequence but well backed, she posted a good second of 15 in handicap hurdle at Fairyhouse (21f) 24 days ago.' },
  "Margaret's Legacy": { info: 'Age: 9| Weight: 10-5| J: Harry Bannister| T: W Greatrex| OR: 124', odds: '33/1', verdict: 'Reluctant individual who came in a below-form twelfth of 22 in Ultima at Cheltenham (25f) 51 days ago. Has a rare run over hurdles (first go in a handicap) here.' },
  'Seaniecon': { info: 'Age: 5| Weight: 10-5| J: Jonjo O\'Neill Jr.| T: J & A O\'Neill| OR: 124| D', odds: '15/2', verdict: 'Lightly-raced sort who bagged maiden hurdle at Hereford in February. Good fifth of 12 in Sefton Hurdle at Aintree (3m) last time and may do better still now handicapping with cheekpieces added.' },
  'Fad Eadrainn': { info: 'Age: 8| Weight: 10-4| J: Simon Torrens| T: P T Foley| OR: 123', odds: '25/1', verdict: 'Scored at Fairyhouse in November and back to form with fifth of 15 in handicap hurdle at Fairyhouse (21f) 24 days ago.' },
  'Icare Desbois': { info: 'Age: 8| Weight: 10-3| J: Cian Quirke| T: D H Kelly| OR: 122', odds: '125/1', verdict: 'Blinkered for 1st time when a below-par third of 5 in conditions hurdle at Clonmel (17f) in January. Significantly up in trip (not bred to stay) with work to do if he\'s to end a long losing run.' },
  'Sign From Above': { info: 'Age: 8| Weight: 10-3| J: Sam Ewing| T: Peter Fahey| OR: 122', odds: '66/1', verdict: 'Last of 10 in Flat handicap at Dundalk (2m) 78 days ago. Switches to hurdles with lots more required.' },
  'The Lovely Man': { info: 'Age: 7| Weight: 10-3| J: Conor Stone-Walsh| T: G P Cromwell| OR: 122| D', odds: '9/1', verdict: 'Gained a third win (including in this sphere) from his last 4 starts in 15-runner handicap chase at Naas (25f) 53 days ago. Back over hurdles and potentially well treated but probably needs more of a test than he\'ll get here.' },
  'Billy Lee Swagger': { info: 'Age: 7| Weight: 10-0| J: Shane O\'Callaghan(5)| T: P J Rothwell| OR: 117| C', odds: '20/1', verdict: 'Out of sorts over hurdles and pulled up in novice chase at Downpatrick (19f) on debut over fences 32 days ago. Blinkers replace usual cheekpieces.' },
  "Bridie's Beau": { info: 'Age: 7| Weight: 10-0| J: Patrick M O\'Brien(5)| T: G P Cromwell| OR: 117| C', odds: '66/1', verdict: 'Course winner but (tongue tied) pulled up in handicap chase at Navan (3m) 40 days ago. Hard to warm to.' },
  'Chance Another One': { info: 'Age: 7| Weight: 10-0| J: Daniel King| T: E Mullins| OR: 115| D', odds: '12/1', verdict: 'Scored 3 times across both codes last season. Back on track when fourth of 13 in handicap chase at Aintree (25f) 19 days ago. Not discounted back over hurdles. RESERVE.' },

  'Ballysax Hank': { info: 'Age: 7| Weight: 11-12| J: James Bowen| T: G P Cromwell| OR: 138', odds: '12/1', verdict: 'Versatile performer shaped better than bare result in a pair of listed handicaps at Leopardstown before seemingly finding 2m on the Old Course at Cheltenham an inadequate test when sixth in the Grand Annual, though he was left with a bit to do.' },
  'Western Diego': { info: 'Age: 9| Weight: 11-11| J: Brian Hayes| T: W P Mullins| OR: 137| D', odds: '25/1', verdict: 'Won a Grade 3 handicap at Fairyhouse earlier in the season and coped well with a return to more speed-favouring conditions in the Grand Annual at Cheltenham, for all his effort looked to be petering out when falling at the last.' },
  'Come Walk With Me': { info: 'Age: 7| Weight: 11-10| J: Donagh Meyler| T: E Cawley| OR: 136', odds: '4/1', verdict: 'Showed improved form to get off the mark in a listed novice handicap at Fairyhouse on his latest start, and with the runner-up giving the form a healthy boost subsequently, he cannot be discounted in his bid to follow up.' },
  'Coral River': { info: 'Age: 7| Weight: 11-7| J: Sean Flanagan| T: R O\'Sullivan| OR: 133| D', odds: '11/1', verdict: 'Useful sort didn\'t need to improve to open his chase account at Clonmel (2.5m) last time. Drop back in trip shouldn\'t be an issue, and he looks on a fair mark ahead of this handicap chase debut.' },
  'Escapeandevade': { info: 'Age: 10| Weight: 11-7| J: Paul O\'Brien| T: Harry Derham| OR: 133| BF| D', odds: '16/1', verdict: 'Plenty of solid form this season but was unable to reel in one that dominated when runner-up for the seventh time in his previous 10 starts at Newbury last time. Finds himself in a much deeper race here, though.' },
  'Raffles Dolce Vita': { info: 'Age: 5| Weight: 11-7| J: J J Slevin| T: T Gibney| OR: 133', odds: '13/2', verdict: 'Became yet another winner to come out of a strong Gowran maiden chase when opening his account with an improved performance at Leopardstown, jumping well to see off Come Walk With Me comfortably and he may have been let-in lightly by the handicapper.' },
  "Path D'oroux": { info: 'Age: 9| Weight: 11-6| J: Ben Harvey| T: G P Cromwell| OR: 132| CD', odds: '80/1', verdict: 'Hasn\'t won since the autumn of 2024 and didn\'t shape as though ready to capitalise on his falling handicap mark when well beaten at Cork earlier this month.' },
  'Release The Beast': { info: 'Age: 7| Weight: 11-6| J: Eoin Staples(5)| T: P Nolan| OR: 132| D', odds: '5/1', verdict: 'Hard to knock his form in handicaps this season, finishing fourth in the Grand Annual at Cheltenham on latest start. He\'s still relatively lightly raced for his age and expected to give another good account.' },
  'The King Of Prs': { info: 'Age: 8| Weight: 11-6| J: Keith Donoghue| T: G P Cromwell| OR: 132| CD', odds: '40/1', verdict: 'Winner of a valuable handicap at Fairyhouse off 2 lb higher last season, and he\'d shaped as though back in form before crashing out as the race was beginning to take shape in the Topham at Aintree. Cheekpieces now go back on.' },
  'Relieved Of Duties': { info: 'Age: 7| Weight: 11-5| J: Jack Kennedy| T: G Elliott| OR: 131| D', odds: '22/1', verdict: 'Hasn\'t kicked on from a promising start over fences, finishing down the field in the Grand Annual last time, though the handicapper has offered some respite on the back of that effort.' },
  'Sky Lord': { info: 'Age: 7| Weight: 11-5| J: Darragh O\'Keeffe| T: H De Bromhead| OR: 131| BF| D', odds: '9/1', verdict: 'Low-mileage 7-y-o is in excellent hands but again failed to convince with his effort off the bridle when third on handicap debut at Cork. Fitting of a first-time tongue strap and the switch to a bigger field could see him in a better light, though.' },
  'Birdie Or Bust': { info: 'Age: 8| Weight: 11-4| J: H Cobden| T: H De Bromhead| OR: 130| D', odds: '33/1', verdict: 'Gave her all when runner-up in a Grade 3 Punchestown novice to end last season and should be closer to that form in first-time cheekpieces here, having looked rusty on reappearance at Fairyhouse.' },
  'Golden Joy': { info: 'Age: 7| Weight: 11-4| J: Danny Gilligan| T: G Elliott| OR: 130', odds: '28/1', verdict: 'Chased home a better-fancied stable when runner-up in a listed handicap at Leopardstown in early-February but this looks a stronger race, and Jack Kennedy looks elsewhere.' },
  'Indiana Jones': { info: 'Age: 10| Weight: 11-4| J: Shane O\'Callaghan(5)| T: M F Morris| OR: 130| CD', odds: '40/1', verdict: 'On a long losing run but exceeded expectations from out of the handicap when fifth in the Topham at Aintree last time. Far from guaranteed to back that up over a much shorter trip, though.' },
  'Jalila Moriviere': { info: 'Age: 7| Weight: 11-4| J: Simon Torrens| T: W P Mullins| OR: 130| D', odds: '18/1', verdict: 'Shaped as though a return to 2m would suit when a useful third in a Grade 3 Novice at Thurles last month. She can have a line put through her latest run (left poorly placed) and looks well worth another chance in a big-field handicap.' },
  'McLaurey': { info: 'Age: 7| Weight: 11-4| J: Mark Walsh| T: E Mullins| OR: 130| D', odds: '6/1', verdict: 'Has caught the eye in recent starts, looking threatening before failing to see out his race in the Plate at Cheltenham (2.5m) latest, and he makes plenty of appeal back down in trip, with first-time tongue strap to boot.' },
  'Petit Tonnerre': { info: 'Age: 8| Weight: 11-2| J: R P McLernon| T: J & A O\'Neill| OR: 128| CD', odds: '16/1', verdict: 'Had the race run to suit when notching a career-best success in this race 12 months ago and connections have probably had one eye on a repeat, now returning off only 1 lb higher with Richie McLernon back in the saddle for the first time since last year\'s success.' },
  'Seskin Flash': { info: 'Age: 7| Weight: 10-9| J: Conor Stone-Walsh| T: J P Dempsey| OR: 121', odds: '20/1', verdict: 'Very much on the up since joining current yard, finishing fourth in a competitive handicap at Leopardstown on St Stephen\'s Day, and there could be more to come on his return.' },
  'Dont Go Yet': { info: 'Age: 12| Weight: 10-3| J: Sarah Kavanagh(7)| T: E Cawley| OR: 115| BF| D', odds: '33/1', verdict: 'Did well to finish third behind a pair who were ridden more prominently in a veterans chase at Wexford last time but finds himself in much deeper waters here.' },
  'Tuckmill': { info: 'Age: 10| Weight: 10-0| J: J J Burke| T: Peter Fahey| OR: 110| D', odds: '125/1', verdict: 'Took a step back in the right direction over hurdles at Downpatrick last time, though will likely find this too competitive, even if back to his best.' },

  'Irish Panther': { info: 'Age: 9| Weight: 11-12| J: Kieren Buckley| T: E & P Harty| OR: 152| D', odds: '15/2', verdict: 'Has taken really well to fences, building on opening Navan success when 1/2-length second to Romeo Coolio in Grade 1 novice at the Leopardstown Christmas meeting. Swerved the Arkle for a sporting tilt at the Champion Chase but his jumping didn\'t hold up. Can make presence felt back in novice company.' },
  "Jacob's Ladder": { info: 'Age: 7| Weight: 11-12| J: Jack Kennedy| T: G Elliott| OR: 150| D', odds: '18/1', verdict: 'Much improved since fitted with cheekpieces, recording his third win over fences in Grade 3 novice at Navan. Just respectable fourth in Grade 1 at Fairyhouse since, however, and needs to raise his game kept to this level.' },
  'Kopek Des Bordes': { info: 'Age: 6| Weight: 11-12| J: Paul Townend| T: W P Mullins| OR: 161| D', odds: '4/11', verdict: 'Winner of the Supreme last season. Had just the one run over fences (cruised clear in a Navan maiden) prior to his second in the Arkle at Cheltenham, likely to have won had he jumped the last better. Superb chance of making amends.' },
  'Pure Steel': { info: 'Age: 6| Weight: 11-12| J: Mark Walsh| T: J J Mangan| OR: 145| CD', odds: '12/1', verdict: 'Won a couple of C&D novices this season and was looking very much at home stepped up to this level until unseating 3 out at Fairyhouse 25 days ago. Remains open to improvement.' },
  'Salvator Mundi': { info: 'Age: 6| Weight: 11-12| J: H Cobden| T: W P Mullins| OR: 149| BF| C| D', odds: '13/2', verdict: 'Won the Grade 1 Top Novices\' Hurdle at Aintree 12 months ago. Has quickly matched that level of form sent chasing this season, easily making all in maiden at Thurles. However, failed to settle when second in Grade 1 novice at Aintree 19 days ago and needs to settle down.' },

  'Bob Olinger': { info: 'Age: 11| Weight: 11-10| J: Darragh O\'Keeffe| T: H De Bromhead| OR: 158| C| D', odds: '4/1', verdict: 'Veteran who was no match for Teahupoo in the Christmas Hurdle on reappearance, but he ran a stormer from a less-than-ideal position when finishing third in defence of his Stayers\' Hurdle crown at Cheltenham and another bold bid is expected.' },
  'Franciscan Rock': { info: 'Age: 9| Weight: 11-10| J: Josh Williamson| T: M F Morris| OR: 140| CD', odds: '28/1', verdict: 'Enhanced a solid record at the Cheltenham Festival when runner-up in the BetMGM handicap there last month but he\'s finished well held in the previous 2 renewals of this event.' },
  'Honesty Policy': { info: 'Age: 6| Weight: 11-10| J: H Cobden| T: G Elliott| OR: 153| BF', odds: '6/1', verdict: 'Grade 1 novice winner who backed up his creditable fifth in the Stayers at Cheltenham when third in the Liverpool Hurdle last time. Neither of those races got to the bottom of him, and he remains with the potential to be a serious force in this division.' },
  'Jimmy Du Seuil': { info: 'Age: 7| Weight: 11-10| J: Paul Townend| T: W P Mullins| OR: 155', odds: '9/1', verdict: 'Very smart 2025 Coral Cup winner who remains unexposed over staying trips, though he has fallen short in Grade 1 company to date, most recently when third in a 2.5 novice chase at Fairyhouse.' },
  'Kawaboomga': { info: 'Age: 6| Weight: 11-10| J: Mark Walsh| T: W P Mullins| OR: 148', odds: '5/1', verdict: 'Lightly-raced 6-y-o who had strong form in maidens last season, and he took a notable step forward from his reappearance when runner-up in a Grade 2 at Fairyhouse (2.5m) earlier this month. Still far from exposed and could prove dangerous if 3m is within his range.' },
  'Meet And Greet': { info: 'Age: 10| Weight: 11-10| J: Phillip Enright| T: O McKiernan| OR: 140', odds: '150/1', verdict: 'Useful hurdler and posted his best effort over fences when runner-up at Down Royal last time. Cheekpieces go on for the return to hurdles, but he\'s likely to be out of his depth, as was the case in this race 12 months ago.' },
  'Teahupoo': { info: 'Age: 9| Weight: 11-10| J: Jack Kennedy| T: G Elliott| OR: 163| BF| CD', odds: '5/4', verdict: 'Again looked the one to beat in this division when an impressive winner of the Christmas Hurdle at Leopardstown. There were mitigating factors for his subsequent sixth in the Stayers at Cheltenham and with first-time blinkers added, he can win this race for the third year on the bounce.' },
  'Jetara': { info: 'Age: 8| Weight: 11-3| J: Sam Ewing| T: Mrs J Harrington| OR: 137| C| D', odds: '20/1', verdict: 'Finished third in the 2025 renewal of this race but hasn\'t looked the same force in recent months, finishing well held in the David Nicholson Mares\' Hurdle at Cheltenham on her latest start.' },

  "Bois D'angos": { info: 'Age: 6| Weight: 12-0| J: Mr F R Buckley(7)| T: J C McConnell', odds: '66/1', verdict: 'Showed the benefit of his initial experience under Rules when landing 7-runner bumper at Limerick (17f, heavy) in March, staying on to lead final 100 yds. Needs another chunk of improvement now taking on stronger opposition.' },
  'Bon Bon Fizz': { info: 'Age: 6| Weight: 12-0| J: Mr J M Halford(7)| T: G Elliott', odds: '6/1', verdict: 'Fell sole start in points/over hurdles prior to making a winning bumper debut in 8-runner event at Thurles (17f, heavy) in March, suited by emphasis on stamina. Has since been bought out of Paul O\'Flynn\'s yard and interesting to see if he\'s as effective under less testing conditions.' },
  'Outofafrika': { info: 'Age: 5| Weight: 12-0| J: Mr D G Lavery| T: G P Cromwell| D', odds: '16/5', verdict: 'Showed the benefit of his initial experience under Rules when landing 7-runner bumper at Fairyhouse (2m, heavy) in February, leading under 2f out and going clear final 1f. Further improvement possible.' },
  'Soul Asylum': { info: 'Age: 5| Weight: 12-0| J: Mr H C Swan| T: G Elliott| CD', odds: '7/2', verdict: 'GBP280,000 Walk In The Park gelding. Runner-up in a point and looked above average when making a successful debut under Rules in a course bumper (2m, heavy) in February. Open to improvement.' },
  'Cowboy Casanova': { info: 'Age: 5| Weight: 11-7| J: Mr D O\'Connor| T: M Bowen', odds: '50/1', verdict: 'EUR58,000 Walk In The Park gelding who finished third on sole outing in points and has shaped well on both bumper starts, including in a first-time hood when third of 7 at Uttoxeter (2m) last month. Has a lot more on his plate here, however.' },
  'Highlander Addict': { info: 'Age: 5| Weight: 11-7| J: Mr D Doyle(7)| T: P J Flynn', odds: '66/1', verdict: 'Built on debut promise when second of 16 in bumper (33/1) at Navan (2m, good to soft) in September, albeit no match for the winner. This is a big step up, however.' },
  "It's Good To Talk": { info: 'Age: 5| Weight: 11-7| J: Mr J L Gleeson| T: E Mullins', odds: '14/1', verdict: 'Caravaggio gelding. Half-brother to numerous winners, including smart multiple bumper winner A Dream To Share, and made a promising start to her career when second in 6-runner bumper at Naas (15f, heavy) on debut in February. Likely to improve for all that this asks for a good deal more.' },
  'Adaboy Mushy': { info: 'Age: 4| Weight: 11-6| J: Mr B T Stone(7)| T: D Queally| D', odds: '9/1', verdict: 'Blue Bresil gelding. Half-brother to 3 winners, including fairly useful hurdler/useful chaser Mahlervous. Overcame inexperience to make a winning debut in 8-runner bumper at Leopardstown (2m, soft) last month and open to improvement with a hood now applied.' },
  'Our Trigger': { info: 'Age: 4| Weight: 11-6| J: Miss J Townend| T: W P Mullins| OR: 119| D', odds: '22/1', verdict: 'Brother to smart hurdler/top-class chaser Gaelic Warrior and looked a good prospect himself when drawing clear to land odds of 2/5 on his Gowran bumper debut in January. Beat only one home in Champion Bumper subsequently, though.' },
  'Quiryn': { info: 'Age: 4| Weight: 11-6| J: Mr P W Mullins| T: W P Mullins| OR: 125| D', odds: '7/4', verdict: 'Sottsass gelding who created an excellent impression when scoring by 9 lengths on his Naas debut (soft) in January. Found his failure to settle early catching up with him late in the Champion Bumper at Cheltenham and probably still has a bigger performance in him.' },
};

function parseSportingLifeRunnerInfo(info = '') {
  const parts = info.split('|').map((part) => part.trim()).filter(Boolean);
  return {
    officialRating: (info.match(/OR:\s*([^|]+)/) || [])[1]?.trim() || '',
    tags: parts.filter((part) => !/^(Age:|Weight:|J:|T:|OR:)/.test(part)),
  };
}

function PunchestownTomorrowView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [payload, setPayload] = useState({ races: [], race_count: 0, settled_count: 0, date: null, last_analysed_at: null });
  const [summaryPayload, setSummaryPayload] = useState({ races: [], race_count: 0, settled_count: 0, date: null, last_analysed_at: null });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [strategyMode, setStrategyMode] = useState('balanced');
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);

  const todayDate = new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
  const lockedFeaturedCourse = '';
  const isFutureMeetingView = false;
  const yesterdayDateObj = new Date(`${todayDate}T12:00:00`);
  yesterdayDateObj.setDate(yesterdayDateObj.getDate() - 1);
  const yesterdayDate = yesterdayDateObj.toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
  const eventLabel = new Date(`${todayDate}T12:00:00`).toLocaleDateString('en-GB', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const loadPunchestown = async () => {
    setLoading(true);
    setError(null);
    try {
      const todayParams = new URLSearchParams({ date: todayDate });
      if (lockedFeaturedCourse) todayParams.set('course', lockedFeaturedCourse);
      // Cache for 5 minutes to improve performance
      const cacheKey = `featured_${todayDate}_${lockedFeaturedCourse || 'auto'}`;
      const todayRes = await fetch(`${API_BASE_URL}/api/picks/featured-meeting?${todayParams.toString()}`, {
        cache: 'default',
        headers: { 'Cache-Control': 'max-age=300' }
      });
      const todayData = await todayRes.json();
      if (!todayData.success) throw new Error(todayData.error || 'Failed to load featured meeting analysis');

      if (isFutureMeetingView) {
        setPayload(todayData);
        setSummaryPayload(todayData);
        setLastUpdated(new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }));
        return;
      }

      // Only fetch yesterday if needed for summary (skip if today data is sufficient)
      const summaryCourse = lockedFeaturedCourse || todayData?.course;
      const yesterdayParams = new URLSearchParams({ date: yesterdayDate });
      if (summaryCourse) yesterdayParams.set('course', summaryCourse);
      const yesterdayRes = await fetch(`${API_BASE_URL}/api/picks/featured-meeting?${yesterdayParams.toString()}`, {
        cache: 'default',
        headers: { 'Cache-Control': 'max-age=300' }
      });
      const yesterdayData = await yesterdayRes.json();

      setPayload(todayData);
      setSummaryPayload(yesterdayData?.success ? yesterdayData : todayData);
      setLastUpdated(new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }));
    } catch (err) {
      setError(err.message || 'Network error while loading featured meeting analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPunchestown();
    // Refresh every 30 minutes (reduced from 15 for better performance)
    const interval = setInterval(loadPunchestown, 30 * 60 * 1000);

    // Only reload on visibility change if page has been hidden for >5 minutes
    let lastLoadTime = Date.now();
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible' && (Date.now() - lastLoadTime) > 5 * 60 * 1000) {
        loadPunchestown();
        lastLoadTime = Date.now();
      }
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    // Removed focus listener - too aggressive, causes constant reloads

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const formatReviewedAt = (value) => {
    if (!value) return 'n/a';
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    }
    return String(value);
  };

  const formatPunchestownTime = (race) => {
    const raw = race?.race_time;
    if (raw) {
      const parsed = new Date(raw);
      if (!Number.isNaN(parsed.getTime())) {
        return parsed.toLocaleTimeString('en-GB', {
          timeZone: 'Europe/Dublin',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        });
      }
      if (typeof raw === 'string' && raw.length >= 16) return raw.slice(11, 16);
    }
    return race?.time_user || 'TBC';
  };

  const parseOddsToDecimal = (oddsValue) => {
    if (oddsValue === null || oddsValue === undefined || oddsValue === '') return null;
    if (typeof oddsValue === 'number' && Number.isFinite(oddsValue) && oddsValue > 0) return oddsValue;
    const text = String(oddsValue).trim();
    if (!text) return null;
    if (text.includes('/')) {
      const [a, b] = text.split('/').map((v) => Number(v));
      if (Number.isFinite(a) && Number.isFinite(b) && b > 0) {
        return Number((a / b + 1).toFixed(2));
      }
    }
    const parsed = Number(text);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  };

  const strategyRunners = (payload.races || [])
    .map((race) => {
      const pick = race?.pick || {};
      const decimalOdds = parseOddsToDecimal(pick.odds);
      return {
        time: formatPunchestownTime(race),
        horse: pick.horse,
        score: Number(pick.score || 0),
        gap: Number(pick.score_gap_to_second || 0),
        confidence: pick.confidence_grade || '',
        decimalOdds,
      };
    })
    .filter((r) => r.horse)
    .sort((a, b) => {
      const edgeA = (a.score || 0) + (a.gap > 0 ? a.gap * 2 : 0);
      const edgeB = (b.score || 0) + (b.gap > 0 ? b.gap * 2 : 0);
      return edgeB - edgeA;
    });

  const topThree = strategyRunners.slice(0, 3);
  const topFour = strategyRunners.slice(0, 4);

  const doubles = topThree.length >= 2
    ? [
        [topThree[0], topThree[1]],
        topThree[2] ? [topThree[0], topThree[2]] : null,
        topThree[2] ? [topThree[1], topThree[2]] : null,
      ].filter(Boolean)
    : [];

  const formatPrice = (n) => (Number.isFinite(n) ? n.toFixed(2) : 'n/a');
  const estimateReturn = (stake, dec) => (Number.isFinite(dec) ? (stake * dec).toFixed(2) : 'n/a');

  const stakeProfiles = {
    conservative: {
      label: 'Conservative',
      singlePts: 0.5,
      doublePts: 0.25,
      treblePts: 0.1,
      note: 'Lower variance, preserve bankroll.',
    },
    balanced: {
      label: 'Balanced',
      singlePts: 1,
      doublePts: 0.5,
      treblePts: 0.2,
      note: 'Default risk profile for steady growth.',
    },
    aggressive: {
      label: 'Aggressive',
      singlePts: 1.5,
      doublePts: 0.75,
      treblePts: 0.35,
      note: 'Higher upside with larger drawdown risk.',
    },
  };

  const activeStakeProfile = stakeProfiles[strategyMode] || stakeProfiles.balanced;

  const ordinal = (n) => {
    const num = Number(n);
    if (!Number.isFinite(num)) return '';
    const mod100 = num % 100;
    if (mod100 >= 11 && mod100 <= 13) return `${num}th`;
    const mod10 = num % 10;
    if (mod10 === 1) return `${num}st`;
    if (mod10 === 2) return `${num}nd`;
    if (mod10 === 3) return `${num}rd`;
    return `${num}th`;
  };

  const deriveOutcomeFromFullResult = (race, pickHorse) => {
    if (!pickHorse) return null;
    const fullResultText = race?.result || '';
    if (!fullResultText) return null;

    const lowerPick = String(pickHorse).toLowerCase();
    const parts = String(fullResultText)
      .split('|')
      .map((p) => p.trim())
      .filter(Boolean);

    for (const part of parts) {
      const match = part.match(/^(\d+)\)\s*(.+)$/);
      if (!match) continue;
      const pos = Number(match[1]);
      const runnerText = match[2].toLowerCase();
      if (!runnerText.includes(lowerPick)) continue;
      if (pos === 1) return 'Win';
      return `Placed (${ordinal(pos)})`;
    }

    return null;
  };

  const summaryIsYesterday = summaryPayload?.date === yesterdayDate;
  const featuredSummaryRows = (summaryPayload.races || []).map((race) => {
    const pick = race?.pick || {};
    const matchedRunner = Array.isArray(race?.runners)
      ? race.runners.find((runner) => runner?.horse === pick?.horse)
      : null;
    const runnerOutcome = (matchedRunner?.outcome || '').toLowerCase();
    const normalized = normalizePickOutcome(pick);
    const derivedOutcome = deriveOutcomeFromFullResult(race, pick?.horse);

    let outcomeCode = 'PENDING';
    let outcomeLabel = 'Pending';
    if (normalized === 'WIN' || runnerOutcome === 'win' || runnerOutcome === 'won') {
      outcomeCode = 'WIN';
      outcomeLabel = 'Win';
    } else if (normalized === 'PLACED' || runnerOutcome === 'placed' || runnerOutcome === 'place') {
      outcomeCode = 'PLACED';
      outcomeLabel = pick?.result ? `Placed (${pick.result})` : 'Placed';
    } else if (normalized === 'LOSS' || runnerOutcome === 'loss' || runnerOutcome === 'lost') {
      outcomeCode = 'LOSS';
      outcomeLabel = 'Lost';
    } else if (race?.is_settled && race?.winner) {
      outcomeCode = String(race.winner) === String(pick?.horse) ? 'WIN' : 'LOSS';
      outcomeLabel = outcomeCode === 'WIN' ? 'Win' : 'Lost';
    }

    if (derivedOutcome) {
      outcomeLabel = derivedOutcome;
      outcomeCode = derivedOutcome.startsWith('Win')
        ? 'WIN'
        : derivedOutcome.startsWith('Placed')
          ? 'PLACED'
          : derivedOutcome.startsWith('Lost')
            ? 'LOSS'
            : outcomeCode;
    }

    return {
      race,
      horse: pick?.horse || '',
      outcomeCode,
      outcomeLabel,
      decimalOdds: parseOddsToDecimal(pick?.odds),
      odds: pick?.odds || '',
    };
  });

  const featuredWins = featuredSummaryRows.filter((row) => row.outcomeCode === 'WIN');
  const featuredPlaces = featuredSummaryRows.filter((row) => row.outcomeCode === 'PLACED');
  const bestFeaturedWinner = featuredWins
    .slice()
    .sort((a, b) => (b.decimalOdds || 0) - (a.decimalOdds || 0))[0] || null;
  const bestFeaturedWinnerOdds = bestFeaturedWinner
    ? (toFractional(bestFeaturedWinner.decimalOdds) || bestFeaturedWinner.odds || '')
    : '';
  const featuredSummaryTotal = featuredSummaryRows.length;
  const featuredTopResults = (summaryPayload.races || [])
    .map((race) => {
      const winnerName = String(race?.winner || '').trim();
      if (winnerName) {
        return {
          raceTime: race?.race_time || race?.time || '',
          winner: winnerName,
        };
      }

      const resultText = String(race?.result || '');
      const firstPlaced = resultText
        .split('|')
        .map((part) => part.trim())
        .find((part) => /^1\)\s*/.test(part));
      if (!firstPlaced) return null;

      return {
        raceTime: race?.race_time || race?.time || '',
        winner: firstPlaced.replace(/^1\)\s*/, '').trim(),
      };
    })
    .filter((entry) => entry?.winner)
    .slice(0, 3);
  const featuredYesterdayLabel = new Date(`${yesterdayDate}T12:00:00Z`).toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });

  const formatFeaturedOdds = (oddsValue) => {
    const decimal = parseOddsToDecimal(oddsValue);
    if (decimal) return toFractional(decimal) || String(oddsValue || '');
    return String(oddsValue || '');
  };

  const todayPickRows = (payload.races || []).map((race) => {
    const pick = race?.pick || {};
    const eachWayPick = race?.each_way_pick || null;
    const pickResult = String(pick?.result || '').trim();
    const normalized = normalizePickOutcome(pick);
    const matchedRunner = Array.isArray(race?.runners)
      ? race.runners.find((runner) => runner?.horse === pick?.horse)
      : null;
    const runnerOutcome = (matchedRunner?.outcome || '').toLowerCase();

    let outcome = 'Pending';
    if (normalized === 'WIN' || runnerOutcome === 'win' || runnerOutcome === 'won') {
      outcome = 'Win';
    } else if (normalized === 'PLACED' || runnerOutcome === 'placed' || runnerOutcome === 'place') {
      outcome = pickResult ? `Placed (${pickResult})` : 'Placed';
    } else if (normalized === 'LOSS' || runnerOutcome === 'loss' || runnerOutcome === 'lost') {
      outcome = 'Lost';
    } else if (race?.is_settled && race?.winner) {
      outcome = String(race.winner) === String(pick?.horse) ? 'Win' : 'Lost';
    }
    const derivedOutcome = deriveOutcomeFromFullResult(race, pick?.horse);
    if (derivedOutcome) outcome = derivedOutcome;

    return {
      time: formatPunchestownTime(race),
      pick: pick?.horse || 'n/a',
      eachWay: eachWayPick?.horse || '',
      odds: formatFeaturedOdds(pick?.odds || race?.odds || ''),
      grade: pick?.confidence_grade || '',
      outcome,
    };
  });

  const punchestownRacecards = (payload.races || []).map((race) => {
    return {
      time: formatPunchestownTime(race),
      title: race.race || race.race_name || `${payload.course || 'Featured meeting'} race`,
      details: [race.course, race.runners_count ? `${race.runners_count} runners` : null].filter(Boolean).join(' | '),
      analysis: null,
      runners: Array.isArray(race.runners)
        ? race.runners.map((runner) => ({
            horse: runner.horse,
            jockey: runner.jockey,
            odds: runner.odds,
            officialRating: runner.official_rating,
          }))
        : [],
      linkedRace: race,
    };
  });

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '56px 20px', color: 'white' }}>
        <div style={{ fontSize: '18px', opacity: 0.85 }}>{`Loading featured meeting ${eventLabel} analysis...`}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ background: 'rgba(239,68,68,0.14)', border: '1px solid rgba(239,68,68,0.45)', borderRadius: '12px', padding: '24px', color: 'white', textAlign: 'center' }}>
        <div style={{ fontWeight: '800', marginBottom: '8px' }}>Could not load featured meeting page</div>
        <div style={{ fontSize: '13px', opacity: 0.85, marginBottom: '14px' }}>{error}</div>
        <button onClick={loadPunchestown} style={{ background: '#059669', border: 'none', borderRadius: '8px', color: 'white', padding: '9px 18px', cursor: 'pointer', fontWeight: '700' }}>Retry</button>
      </div>
    );
  }

  const featuredDisplayPayload = summaryIsYesterday ? summaryPayload : payload;
  const featuredCourseLabel = lockedFeaturedCourse || featuredDisplayPayload?.course || payload?.course || 'Featured Meeting';
  const featuredDateLabel = summaryIsYesterday ? (summaryPayload?.date || yesterdayDate) : (payload?.date || todayDate);
  const featuredMeetingDescriptor = buildFeaturedMeetingTabLabel(
    lockedFeaturedCourse || featuredDisplayPayload?.course || payload?.course,
    featuredDateLabel
  );
  const featuredPageTitle = 'Featured Meet';

  return (
    <div style={{ padding: isMobile ? '0 2px' : '0' }}>
      <div style={{ background: 'linear-gradient(135deg,#065f46 0%,#064e3b 100%)', border: '2px solid rgba(52,211,153,0.45)', borderRadius: '12px', padding: isMobile ? '16px 14px' : '22px 24px', marginBottom: '20px', color: 'white' }}>
        <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1.2px', color: '#6ee7b7', marginBottom: '6px' }}>Featured Daily Meeting</div>
        <div style={{ fontSize: isMobile ? '20px' : '24px', fontWeight: '800', marginBottom: '8px', lineHeight: 1.2 }}>{featuredPageTitle}</div>
        <div style={{ fontSize: isMobile ? '13px' : '14px', fontWeight: '700', color: 'rgba(255,255,255,0.84)', marginBottom: '8px' }}>{featuredMeetingDescriptor}</div>
        <div style={{ fontSize: isMobile ? '12px' : '13px', color: 'rgba(255,255,255,0.78)', lineHeight: 1.5 }}>
          Auto-selected race-by-race card using the standard comprehensive scoring logic. At weekends the highest-profile UK or Irish meeting is chosen; on weekdays the top Irish meeting is featured. Refreshed throughout the day as analysis reruns and results settle.
        </div>
        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', marginTop: '14px' }}>
          <span style={{ background: 'rgba(255,255,255,0.14)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '7px', padding: '4px 10px', fontSize: '12px' }}>Course: {featuredCourseLabel || 'n/a'}</span>
          <span style={{ background: 'rgba(255,255,255,0.14)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '7px', padding: '4px 10px', fontSize: '12px' }}>Date: {featuredDateLabel || 'n/a'}</span>
          <span style={{ background: 'rgba(255,255,255,0.14)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '7px', padding: '4px 10px', fontSize: '12px' }}>Races: {featuredDisplayPayload?.race_count || 0}</span>
          <span style={{ background: 'rgba(255,255,255,0.14)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '7px', padding: '4px 10px', fontSize: '12px' }}>Settled: {featuredDisplayPayload?.settled_count || 0}</span>
        </div>
        {featuredDisplayPayload?.meeting_reason && (
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'rgba(255,255,255,0.74)', lineHeight: 1.5 }}>
            {featuredDisplayPayload.meeting_reason}
          </div>
        )}
        <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.65)' }}>
            {lastUpdated ? `Last refreshed ${lastUpdated}` : 'Not refreshed yet'}
            {payload.last_analysed_at ? ` · Analysis timestamp ${payload.last_analysed_at}` : ''}
          </div>
          <button onClick={loadPunchestown} style={{ background: 'rgba(255,255,255,0.16)', border: '1px solid rgba(255,255,255,0.32)', borderRadius: '8px', color: 'white', padding: '8px 16px', cursor: 'pointer', fontSize: '13px', fontWeight: '700' }}>Refresh</button>
        </div>
        {payload.featured_lock_active && payload.featured_locked_at && (
          <div style={{ marginTop: '10px' }}>
            <span style={{ background: 'rgba(251,191,36,0.18)', border: '1px solid rgba(251,191,36,0.5)', borderRadius: '7px', padding: '5px 12px', fontSize: '12px', color: '#fbbf24', fontWeight: '700' }}>
              {`🔒 Locked at ${new Date(payload.featured_locked_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })} UTC – picks frozen for the day`}
            </span>
          </div>
        )}
      </div>

      <div style={{
        maxWidth: '100%', margin: '0 0 24px', padding: isMobile ? '20px 16px' : '32px 28px',
        background: 'linear-gradient(135deg, rgba(52,211,153,0.18), rgba(16,185,129,0.12))',
        border: '2px solid rgba(52,211,153,0.4)', borderRadius: '16px',
        boxShadow: '0 8px 24px rgba(52,211,153,0.15)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '16px' }}>
          <span style={{ fontSize: '13px', fontWeight: '900', color: '#34d399', background: 'rgba(5,150,105,0.25)', border: '1.5px solid rgba(52,211,153,0.5)', padding: '4px 14px', borderRadius: '999px', letterSpacing: '1.2px', textTransform: 'uppercase' }}>🏆 Featured Snapshot</span>
        </div>
        <div style={{ fontSize: isMobile ? '48px' : '64px', textAlign: 'center', marginBottom: '12px' }}>🏇</div>
        <div style={{ color: 'rgba(255,255,255,0.95)', fontSize: isMobile ? '16px' : '18px', fontWeight: '600', lineHeight: '1.6', textAlign: 'center', maxWidth: '800px', margin: '0 auto' }}>
          {summaryIsYesterday && bestFeaturedWinner
            ? <>
                Best news: <span style={{ color: '#fbbf24', fontWeight: '900' }}>{bestFeaturedWinner.horse}</span> landed
                {bestFeaturedWinnerOdds ? <> at <span style={{ color: '#34d399', fontWeight: '900', fontSize: '16px' }}>{bestFeaturedWinnerOdds}</span></> : ''}
                {' '}on yesterday&apos;s featured card.
                <span style={{ marginLeft: '6px' }}>
                  {`Yesterday (${featuredYesterdayLabel}): `}
                  <span style={{ color: '#fbbf24', fontWeight: '900' }}>{featuredWins.length} winner{featuredWins.length === 1 ? '' : 's'}</span>
                  {' & '}
                  <span style={{ color: '#60a5fa', fontWeight: '900' }}>{featuredPlaces.length} placed</span>
                  {` out of ${featuredSummaryTotal}.`}
                </span>
              </>
            : summaryIsYesterday
              ? <>
                  {featuredTopResults.length > 0
                    ? <>
                        Yesterday&apos;s top results ({featuredYesterdayLabel}):{' '}
                        {featuredTopResults.map((entry, idx) => (
                          <span key={`featured_top_${entry.raceTime}_${entry.winner}`}>
                            {idx > 0 ? ' · ' : ''}
                            <span style={{ color: '#93c5fd', fontWeight: '800' }}>{entry.raceTime || 'Result'}</span>
                            {' '}
                            <span style={{ color: '#fbbf24', fontWeight: '900' }}>{entry.winner}</span>
                          </span>
                        ))}
                      </>
                    : <>
                        Featured meeting review: yesterday&apos;s top results are pending settlement data.
                      </>}
                </>
              : <>
                  Featured meeting picks stay separate from ROI, commentary, and the results page unless the same runner also qualifies as one of the ranked daily picks.
                </>}
        </div>
        <div style={{ fontSize: isMobile ? '14px' : '16px', textAlign: 'center', marginTop: '16px' }}>🔥</div>
      </div>

      {/* Race Picks Summary */}
      <div style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.16)', borderRadius: '12px', padding: '12px 14px', marginBottom: '16px' }}>
        <div style={{ fontSize: '14px', fontWeight: '800', color: 'white', marginBottom: '12px' }}>Race Picks Summary</div>
        <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.72)', lineHeight: 1.55, marginBottom: '12px' }}>
          Featured-only meeting picks are tracked here in their own summary. They do not count toward ROI or appear on the main results page unless the same horse is also promoted into the ranked daily picks list.
        </div>

        {/* Today's picks */}
        {todayPickRows.length > 0 && (
          <>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: '#fbbf24', marginBottom: '8px' }}>{`${featuredCourseLabel || 'Featured meeting'} (${payload.date || todayDate})`}</div>
            {isMobile ? (
              <div style={{ display: 'grid', gap: '8px', marginBottom: '16px' }}>
                {todayPickRows.map((row) => {
                  const isWin = String(row.outcome).startsWith('Win');
                  const isPlaced = String(row.outcome).startsWith('Placed');
                  const isLost = String(row.outcome).startsWith('Lost');
                  const badgeStyle = isWin
                    ? { background: 'rgba(16,185,129,0.16)', border: '1px solid rgba(16,185,129,0.35)', color: '#a7f3d0' }
                    : isPlaced
                      ? { background: 'rgba(59,130,246,0.16)', border: '1px solid rgba(59,130,246,0.35)', color: '#bfdbfe' }
                      : isLost
                        ? { background: 'rgba(239,68,68,0.14)', border: '1px solid rgba(239,68,68,0.35)', color: '#fecaca' }
                        : { background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.35)', color: '#fde68a' };
                  return (
                    <div key={`today_${row.time}_${row.pick}`} style={{ background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.18)', borderRadius: '8px', padding: '9px 10px' }}>
                      <div style={{ display: 'grid', gap: '5px', fontSize: '12px' }}>
                        <div style={{ color: 'rgba(255,255,255,0.72)' }}>Race: <strong style={{ color: 'white' }}>{row.time}</strong></div>
                        <div style={{ color: 'rgba(255,255,255,0.72)' }}>Pick: <strong style={{ color: 'white' }}>{row.pick}</strong></div>
                        <div style={{ color: 'rgba(255,255,255,0.72)' }}>Odds: <strong style={{ color: '#fde68a' }}>{row.odds || '—'}</strong></div>
                        <div style={{ color: 'rgba(255,255,255,0.72)' }}>EW Cover: <strong style={{ color: row.eachWay ? '#fde68a' : 'rgba(255,255,255,0.6)' }}>{row.eachWay || '—'}</strong></div>
                        <div style={{ color: 'rgba(255,255,255,0.72)' }}>
                          Result: <span style={{ ...badgeStyle, borderRadius: '999px', padding: '2px 8px', fontSize: '11px', fontWeight: '700' }}>{row.outcome}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '460px' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', fontSize: '11px', color: 'rgba(255,255,255,0.72)', padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.14)' }}>Race</th>
                      <th style={{ textAlign: 'left', fontSize: '11px', color: 'rgba(255,255,255,0.72)', padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.14)' }}>Pick</th>
                      <th style={{ textAlign: 'left', fontSize: '11px', color: 'rgba(255,255,255,0.72)', padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.14)' }}>Odds</th>
                      <th style={{ textAlign: 'left', fontSize: '11px', color: 'rgba(255,255,255,0.72)', padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.14)' }}>EW Cover</th>
                      <th style={{ textAlign: 'left', fontSize: '11px', color: 'rgba(255,255,255,0.72)', padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.14)' }}>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {todayPickRows.map((row) => {
                      const isWin = String(row.outcome).startsWith('Win');
                      const isPlaced = String(row.outcome).startsWith('Placed');
                      const isLost = String(row.outcome).startsWith('Lost');
                      const badgeStyle = isWin
                        ? { background: 'rgba(16,185,129,0.16)', border: '1px solid rgba(16,185,129,0.35)', color: '#a7f3d0' }
                        : isPlaced
                          ? { background: 'rgba(59,130,246,0.16)', border: '1px solid rgba(59,130,246,0.35)', color: '#bfdbfe' }
                          : isLost
                            ? { background: 'rgba(239,68,68,0.14)', border: '1px solid rgba(239,68,68,0.35)', color: '#fecaca' }
                            : { background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.35)', color: '#fde68a' };
                      return (
                        <tr key={`today_${row.time}_${row.pick}`}>
                          <td style={{ padding: '7px 8px', fontSize: '12px', color: 'white', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>{row.time}</td>
                          <td style={{ padding: '7px 8px', fontSize: '12px', color: 'rgba(255,255,255,0.86)', borderBottom: '1px solid rgba(255,255,255,0.08)', fontWeight: '700' }}>{row.pick}</td>
                          <td style={{ padding: '7px 8px', fontSize: '12px', color: '#fde68a', borderBottom: '1px solid rgba(255,255,255,0.08)', fontWeight: '700' }}>{row.odds || '—'}</td>
                          <td style={{ padding: '7px 8px', fontSize: '12px', color: row.eachWay ? '#fde68a' : 'rgba(255,255,255,0.45)', borderBottom: '1px solid rgba(255,255,255,0.08)', fontWeight: row.eachWay ? '700' : '400' }}>
                            {row.eachWay || '—'}
                          </td>
                          <td style={{ padding: '7px 8px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                            <span style={{ ...badgeStyle, borderRadius: '999px', padding: '2px 8px', fontSize: '11px', fontWeight: '700' }}>{row.outcome}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

      </div>

      {/* Betting Strategy section removed */}
      <div style={{ display: 'none', background: 'linear-gradient(135deg,rgba(30,64,175,0.22) 0%,rgba(22,101,52,0.2) 100%)', border: '1px solid rgba(147,197,253,0.35)', borderRadius: '12px', padding: '14px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '10px' }}>
          <div style={{ fontSize: '15px', fontWeight: '800', color: 'white' }}>Betting Strategy: Singles, Doubles & Multiples</div>
          <span style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '999px', padding: '2px 9px', fontSize: '11px', color: 'rgba(255,255,255,0.82)' }}>
            Strategy built from live model picks
          </span>
        </div>

        <div style={{ display: 'flex', gap: '7px', flexWrap: 'wrap', marginBottom: '10px' }}>
          {['conservative', 'balanced', 'aggressive'].map((mode) => (
            <button
              key={mode}
              onClick={() => setStrategyMode(mode)}
              style={{
                background: strategyMode === mode ? 'rgba(59,130,246,0.3)' : 'rgba(255,255,255,0.06)',
                border: strategyMode === mode ? '1px solid rgba(147,197,253,0.9)' : '1px solid rgba(255,255,255,0.2)',
                borderRadius: '999px',
                color: 'white',
                padding: '5px 11px',
                fontSize: '11px',
                fontWeight: strategyMode === mode ? '800' : '600',
                cursor: 'pointer',
              }}
            >
              {stakeProfiles[mode].label}
            </button>
          ))}
          <span style={{ alignSelf: 'center', fontSize: '11px', color: 'rgba(255,255,255,0.7)' }}>
            {activeStakeProfile.note}
          </span>
        </div>

        {strategyRunners.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit,minmax(240px,1fr))', gap: '10px' }}>
            <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#bfdbfe', fontWeight: '800', marginBottom: '6px' }}>Singles Plan</div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.78)', lineHeight: 1.5 }}>
                {activeStakeProfile.singlePts}pt win single on each model pick ({strategyRunners.length} races). Consider half-stake for picks with score below 70.
              </div>
              {(payload.races || []).some((race) => race?.each_way_pick) && (
                <div style={{ marginTop: '7px', fontSize: '11px', color: '#fde68a', lineHeight: 1.45 }}>
                  Short-price races below also show a separate each-way cover where the card has a credible alternative.
                </div>
              )}
              <div style={{ marginTop: '7px', fontSize: '11px', color: 'rgba(255,255,255,0.7)' }}>
                Anchor pick: <strong style={{ color: 'white' }}>{strategyRunners[0]?.horse || 'n/a'}</strong> ({strategyRunners[0]?.time || 'n/a'})
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#a7f3d0', fontWeight: '800', marginBottom: '6px' }}>Doubles (Top Edge Picks)</div>
              {doubles.length > 0 ? doubles.map((pair, idx) => {
                const combined = (pair[0]?.decimalOdds || 0) * (pair[1]?.decimalOdds || 0);
                return (
                  <div key={`double_${idx}`} style={{ fontSize: '11px', color: 'rgba(255,255,255,0.82)', marginBottom: '5px', lineHeight: 1.5 }}>
                    {pair[0].time} {pair[0].horse} + {pair[1].time} {pair[1].horse}
                    <div style={{ color: 'rgba(255,255,255,0.62)' }}>
                      Approx decimal: {formatPrice(combined)} | {activeStakeProfile.doublePts}pt est return: {estimateReturn(activeStakeProfile.doublePts, combined)}pts
                    </div>
                  </div>
                );
              }) : <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.62)' }}>Need at least 2 picks for doubles.</div>}
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#fde68a', fontWeight: '800', marginBottom: '6px' }}>Multiples</div>
              {topThree.length >= 3 ? (
                <>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.82)', lineHeight: 1.5 }}>
                    Treble: {topThree.map((r) => `${r.time} ${r.horse}`).join(' + ')}
                  </div>
                  <div style={{ marginTop: '4px', fontSize: '11px', color: 'rgba(255,255,255,0.62)' }}>
                    Approx decimal: {formatPrice((topThree[0].decimalOdds || 0) * (topThree[1].decimalOdds || 0) * (topThree[2].decimalOdds || 0))} | {activeStakeProfile.treblePts}pt est return: {estimateReturn(activeStakeProfile.treblePts, (topThree[0].decimalOdds || 0) * (topThree[1].decimalOdds || 0) * (topThree[2].decimalOdds || 0))}pts
                  </div>
                </>
              ) : (
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.62)' }}>Need at least 3 picks for a treble.</div>
              )}
              {topFour.length >= 4 && (
                <div style={{ marginTop: '8px', fontSize: '11px', color: 'rgba(255,255,255,0.78)', lineHeight: 1.5 }}>
                  Yankee option (11 bets) on top 4 picks for broader coverage and upside.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>Strategy will appear once picks load.</div>
        )}
      </div>

      <div style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '12px', padding: isMobile ? '12px' : '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <div style={{ fontSize: '15px', fontWeight: '800', color: 'white' }}>Full Racecard Details</div>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <span style={{ background: 'rgba(16,185,129,0.16)', border: '1px solid rgba(16,185,129,0.35)', borderRadius: '6px', padding: '3px 10px', fontSize: '12px', color: '#a7f3d0' }}>Course: {featuredCourseLabel || 'n/a'}</span>
          <span style={{ background: 'rgba(59,130,246,0.14)', border: '1px solid rgba(59,130,246,0.35)', borderRadius: '6px', padding: '3px 10px', fontSize: '12px', color: '#bfdbfe' }}>Selection: Upcoming major-race meeting</span>
          <span style={{ background: 'rgba(234,179,8,0.14)', border: '1px solid rgba(234,179,8,0.35)', borderRadius: '6px', padding: '3px 10px', fontSize: '12px', color: '#fde68a' }}>Races loaded: {payload.race_count || 0}</span>
        </div>

        <div style={{ display: 'grid', gap: '8px' }}>
          {punchestownRacecards.length === 0 && (
            <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', fontSize: '12px', color: 'rgba(255,255,255,0.72)' }}>
              Awaiting today's featured meeting racecards and picks. Refresh shortly.
            </div>
          )}
          {punchestownRacecards.map((card) => {
            const cardAnalysis = card.analysis || null;
            const linkedRace = card.linkedRace || (payload.races || []).find((race) => {
              const rt = formatPunchestownTime(race);
              return rt === card.time;
            });
            const fullResultText = linkedRace?.result || null;
            const linkedPick = linkedRace?.pick || null;
            const linkedEachWay = linkedRace?.each_way_pick || null;
            const raceReviewedAt = linkedRace?.last_reviewed_at || null;
            const pickReviewedAt = linkedPick?.last_reviewed_at || raceReviewedAt || null;
            const scoredRunners = Array.isArray(linkedRace?.runners)
              ? [...linkedRace.runners].sort((a, b) => (Number(b.score || 0) - Number(a.score || 0)))
              : [];

            return (
              <div key={card.time} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '10px', padding: isMobile ? '10px' : '10px 12px' }}>
                <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'space-between', alignItems: isMobile ? 'stretch' : 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <div>
                    <div style={{ fontSize: '14px', color: 'white', fontWeight: '800' }}>{card.time} - {card.title}</div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.75)', marginTop: '3px' }}>{card.details}</div>
                    {cardAnalysis && (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                        {cardAnalysis.status && (
                          <span style={{ background: 'rgba(16,185,129,0.14)', border: '1px solid rgba(16,185,129,0.28)', borderRadius: '999px', padding: '2px 8px', fontSize: '11px', color: '#a7f3d0', fontWeight: '700' }}>
                            {cardAnalysis.status}
                          </span>
                        )}
                        {cardAnalysis.going && (
                          <span style={{ background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.28)', borderRadius: '999px', padding: '2px 8px', fontSize: '11px', color: '#fde68a' }}>
                            Going: {cardAnalysis.going}
                          </span>
                        )}
                        {cardAnalysis.surface && (
                          <span style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.28)', borderRadius: '999px', padding: '2px 8px', fontSize: '11px', color: '#bfdbfe' }}>
                            Surface: {cardAnalysis.surface}
                          </span>
                        )}
                        {cardAnalysis.offTime && (
                          <span style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: '999px', padding: '2px 8px', fontSize: '11px', color: 'rgba(255,255,255,0.72)' }}>
                            Off: {cardAnalysis.offTime}
                          </span>
                        )}
                        {cardAnalysis.winningTime && (
                          <span style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: '999px', padding: '2px 8px', fontSize: '11px', color: 'rgba(255,255,255,0.72)' }}>
                            Winning time: {cardAnalysis.winningTime}
                          </span>
                        )}
                      </div>
                    )}
                    {fullResultText && (
                      <div style={{ marginTop: '8px', fontSize: '12px', color: 'rgba(255,255,255,0.84)', lineHeight: 1.45 }}>
                        <strong style={{ color: '#fde68a' }}>Full Result:</strong> {fullResultText}
                      </div>
                    )}
                    {Array.isArray(card.runners) && card.runners.length > 0 && (
                      <details style={{ marginTop: '8px' }}>
                        <summary style={{ cursor: 'pointer', fontSize: '12px', color: '#bfdbfe', fontWeight: '700' }}>
                          Runners & riders ({card.runners.length})
                        </summary>
                        <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit,minmax(210px,1fr))', gap: '6px' }}>
                          {card.runners.map((runner, idx) => {
                            const extra = PUNCHESTOWN_RUNNER_DETAILS[runner.horse] || {};
                            const harvested = PUNCHESTOWN_RUNNER_ANALYSIS[runner.horse] || {};
                            const parsedHarvested = parseSportingLifeRunnerInfo(harvested.info || '');
                            const runnerOdds = runner.odds || harvested.odds || '';
                            const runnerOfficialRating = runner.officialRating || parsedHarvested.officialRating || '';
                            const runnerTags = Array.isArray(runner.tags) && runner.tags.length ? runner.tags : parsedHarvested.tags;
                            const runnerVerdict = runner.analysis || harvested.verdict || '';
                            return (
                              <div key={`${card.time}_${idx}`} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', padding: '6px 8px', fontSize: '11px', color: 'rgba(255,255,255,0.83)' }}>
                                <strong style={{ color: 'white' }}>{runner.horse}</strong>
                                <div style={{ marginTop: '2px', color: 'rgba(255,255,255,0.72)' }}>Jockey: {runner.jockey}</div>
                                <div style={{ marginTop: '2px', color: 'rgba(255,255,255,0.72)' }}>Trainer: {extra.trainer || 'n/a'}</div>
                                {(extra.age || extra.weight) && (
                                  <div style={{ marginTop: '2px', color: 'rgba(255,255,255,0.6)' }}>
                                    {extra.age ? `Age ${extra.age}` : ''}
                                    {extra.age && extra.weight ? ' | ' : ''}
                                    {extra.weight ? `Wt ${extra.weight}` : ''}
                                  </div>
                                )}
                                {(runnerOdds || runnerOfficialRating || (Array.isArray(runnerTags) && runnerTags.length > 0)) && (
                                  <div style={{ marginTop: '4px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                    {runnerOdds && (
                                      <span style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.28)', borderRadius: '999px', padding: '1px 6px', fontSize: '10px', color: '#bfdbfe', fontWeight: '700' }}>
                                        Odds: {runnerOdds}
                                      </span>
                                    )}
                                    {runnerOfficialRating && (
                                      <span style={{ background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.28)', borderRadius: '999px', padding: '1px 6px', fontSize: '10px', color: '#fde68a', fontWeight: '700' }}>
                                        OR: {runnerOfficialRating}
                                      </span>
                                    )}
                                    {Array.isArray(runnerTags) && runnerTags.map((tag) => (
                                      <span key={tag} style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.28)', borderRadius: '999px', padding: '1px 6px', fontSize: '10px', color: '#a7f3d0', fontWeight: '700' }}>
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                )}
                                {runnerVerdict && (
                                  <div style={{ marginTop: '4px', color: 'rgba(255,255,255,0.68)', lineHeight: 1.45 }}>
                                    {runnerVerdict}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </details>
                    )}
                  </div>
                  {linkedPick ? (
                    <div style={{ display: 'grid', gap: '8px', maxWidth: isMobile ? '100%' : '520px', width: isMobile ? '100%' : 'auto' }}>
                      <span style={{ background: 'linear-gradient(135deg,#16a34a 0%,#65a30d 100%)', border: '2px solid rgba(190,242,100,0.9)', borderRadius: '10px', padding: isMobile ? '7px 10px' : '8px 14px', fontSize: isMobile ? '13px' : '16px', color: '#f7fee7', fontWeight: '900', letterSpacing: '0.3px', textTransform: 'uppercase', boxShadow: '0 6px 18px rgba(132,204,22,0.35)', justifySelf: 'start' }}>
                        Model Pick: {linkedPick.horse || 'n/a'}
                      </span>

                      <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.22)', borderRadius: '8px', padding: '8px 10px' }}>
                        <div style={{ fontSize: '11px', color: '#a7f3d0', fontWeight: '700', marginBottom: '5px' }}>Why this pick</div>
                        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                          {linkedPick.pick_rationale || 'Top model score for this race.'}
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                          <span style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#bfdbfe', fontWeight: '700' }}>
                            Score: {linkedPick.score ?? 'n/a'}
                          </span>
                          {linkedPick.score_gap_to_second !== null && linkedPick.score_gap_to_second !== undefined && (
                            <span style={{ background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#fde68a', fontWeight: '700' }}>
                              Gap to 2nd: +{linkedPick.score_gap_to_second}
                            </span>
                          )}
                          {linkedPick.confidence_grade && (
                            <span style={{ background: 'rgba(168,85,247,0.12)', border: '1px solid rgba(168,85,247,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#e9d5ff', fontWeight: '700' }}>
                              {linkedPick.confidence_grade}
                            </span>
                          )}
                        </div>
                        {pickReviewedAt && (
                          <div style={{ marginTop: '6px', fontSize: '10px', color: 'rgba(255,255,255,0.55)' }}>
                            Pick last reviewed: {formatReviewedAt(pickReviewedAt)}
                          </div>
                        )}
                      </div>

                      {linkedEachWay && (
                        <div style={{ background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.24)', borderRadius: '8px', padding: '8px 10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                            <div style={{ fontSize: '11px', color: '#fde68a', fontWeight: '700' }}>
                              Each-Way Cover: {linkedEachWay.horse || 'n/a'}
                            </div>
                            <span style={{ background: 'rgba(234,179,8,0.16)', border: '1px solid rgba(234,179,8,0.32)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#fde68a', fontWeight: '700' }}>
                              {linkedEachWay.place_terms || 'Each Way'}
                            </span>
                          </div>
                          <div style={{ marginTop: '5px', fontSize: '11px', color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                            {linkedEachWay.pick_rationale || 'Short-priced main pick, so this is the preferred each-way alternative.'}
                          </div>
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                            {linkedEachWay.odds && (
                              <span style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#bfdbfe', fontWeight: '700' }}>
                                Odds: {linkedEachWay.odds}
                              </span>
                            )}
                            {linkedEachWay.score !== null && linkedEachWay.score !== undefined && (
                              <span style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#a7f3d0', fontWeight: '700' }}>
                                Score: {linkedEachWay.score}
                              </span>
                            )}
                            {linkedEachWay.score_gap_to_second !== null && linkedEachWay.score_gap_to_second !== undefined && (
                              <span style={{ background: 'rgba(168,85,247,0.12)', border: '1px solid rgba(168,85,247,0.28)', borderRadius: '999px', padding: '1px 7px', fontSize: '10px', color: '#e9d5ff', fontWeight: '700' }}>
                                Behind main pick: {linkedEachWay.score_gap_to_second} pts
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {scoredRunners.length > 0 && (
                        <details>
                          <summary style={{ cursor: 'pointer', fontSize: '11px', color: '#bfdbfe', fontWeight: '700' }}>
                            Pick score vs all runners ({scoredRunners.length})
                          </summary>
                          <div style={{ marginTop: '7px', display: 'grid', gap: '5px' }}>
                            {scoredRunners.map((r, scoreIdx) => (
                              <div key={`${card.time}_score_${r.horse || scoreIdx}`} style={{ display: 'grid', gridTemplateColumns: isMobile ? '24px 1fr auto' : '28px 1fr auto auto', gap: '6px', alignItems: 'center', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '5px 7px', fontSize: '11px' }}>
                                <span style={{ color: 'rgba(255,255,255,0.65)', fontWeight: '700' }}>#{r.rank || (scoreIdx + 1)}</span>
                                <span style={{ color: 'white', fontWeight: linkedPick.horse === r.horse ? '800' : '600' }}>{r.horse}</span>
                                <span style={{ color: '#bfdbfe', fontWeight: '700' }}>{r.score ?? 'n/a'}</span>
                                {!isMobile && <span style={{ color: 'rgba(255,255,255,0.65)' }}>{r.odds || ''}</span>}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  ) : (
                    <span style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', padding: '3px 10px', fontSize: '11px', color: 'rgba(255,255,255,0.65)' }}>
                      Model pick pending
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <LegalDisclaimerCard />
    </div>
  );
}

function MajorRacesView() {
  const [filter,   setFilter]   = useState('all');
  const [showPast, setShowPast] = useState(false);
  const [analyses, setAnalyses] = useState({});
  const [featuredMeetingData, setFeaturedMeetingData] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(true);
  const [expandedRace, setExpandedRace] = useState(null);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Fetch early-bird analyses
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/major-race-analysis`)
      .then(r => r.json())
      .then(d => {
        if (d.success && d.analyses) {
          const map = {};
          d.analyses.forEach(a => { map[a.bet_id] = a; });
          setAnalyses(map);
        }
      })
      .catch(() => {})
      .finally(() => setAnalysisLoading(false));
  }, []);

  // Fetch current featured-meeting snapshot so today's major race card stays in sync.
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/picks/featured-meeting`, {
      cache: 'default',
      headers: { 'Cache-Control': 'max-age=300' }
    })
      .then(r => r.json())
      .then(d => {
        if (d?.success) setFeaturedMeetingData(d);
      })
      .catch(() => {});
  }, []);

  const normHorseName = (v) => String(v || '').toLowerCase().replace(/[^a-z0-9]/g, '');

  const formatPickMadeAt = (value) => {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed.toLocaleString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Europe/London',
      timeZoneName: 'short',
    });
  };

  const getSyncedMajorAnalysis = (race, analysis) => {
    if (!analysis) return analysis;
    const featuredCourse = String(featuredMeetingData?.course || '').trim();
    const featuredDate = String(featuredMeetingData?.date || '').slice(0, 10);
    if (!featuredCourse || !featuredDate) return analysis;
    if (featuredDate !== race.date) return analysis;
    if (featuredCourse.toLowerCase() !== String(race.meeting || '').toLowerCase()) return analysis;

    const featuredRaces = Array.isArray(featuredMeetingData?.races) ? featuredMeetingData.races : [];
    if (!featuredRaces.length) return analysis;

    const majorRunnerSet = new Set(
      (Array.isArray(analysis.all_runners) ? analysis.all_runners : [])
        .map((runner) => normHorseName(runner?.name || runner?.horse))
        .filter(Boolean)
    );
    if (!majorRunnerSet.size) return analysis;

    let bestMatch = null;
    let bestOverlap = 0;

    featuredRaces.forEach((fr) => {
      const runners = Array.isArray(fr?.runners) ? fr.runners : [];
      const overlap = runners.reduce((acc, runner) => {
        const key = normHorseName(runner?.horse || runner?.name);
        return key && majorRunnerSet.has(key) ? acc + 1 : acc;
      }, 0);
      if (overlap > bestOverlap) {
        bestOverlap = overlap;
        bestMatch = fr;
      }
    });

    // Require a real overlap to avoid syncing the wrong race.
    if (!bestMatch || bestOverlap < 2) return analysis;

    const ranked = (Array.isArray(bestMatch.runners) ? bestMatch.runners : [])
      .map((runner) => ({
        name: runner?.horse || runner?.name || '',
        score: Number(runner?.score || 0),
        odds_display: runner?.odds || '',
      }))
      .filter((runner) => runner.name)
      .sort((a, b) => b.score - a.score);

    if (!ranked.length) return analysis;

    const livePick = ranked[0];
    const liveReasons = Array.isArray(bestMatch?.pick?.selection_reasons)
      ? bestMatch.pick.selection_reasons.slice(0, 3)
      : (analysis.top_pick_factors || []);

    return {
      ...analysis,
      top_pick: livePick.name,
      top_pick_odds: livePick.odds_display || analysis.top_pick_odds,
      top_pick_score: livePick.score,
      top3: ranked.slice(0, 3),
      total_horses: ranked.length,
      analysed_at: bestMatch?.last_reviewed_at || analysis.analysed_at,
      top_pick_factors: liveReasons,
    };
  };

  const filtered = MAJOR_RACES.filter(r => {
    if (!showPast && isPast(r.date)) return false;
    if (filter === 'NH')        return r.type === 'NH';
    if (filter === 'Flat')      return r.type === 'Flat';
    if (filter === 'highlight') return r.highlight;
    return true;
  });

  const grouped       = groupByMeeting(filtered);
  const upcomingCount = MAJOR_RACES.filter(r => !isPast(r.date)).length;
  const nextRace      = MAJOR_RACES.filter(r => !isPast(r.date)).sort((a,b) => a.date.localeCompare(b.date))[0];

  const meetingColour = m => ({
    Aintree:'#c2410c', Punchestown:'#047857', Newmarket:'#1d4ed8', Epsom:'#7c3aed',
    'Royal Ascot':'#b45309', Goodwood:'#065f46', York:'#1e40af', Doncaster:'#3f3f46',
    Ascot:'#92400e', Sandown:'#0f766e', Chester:'#6b21a8', Ayr:'#064e3b',
  }[m] || '#374151');

  return (
    <div>
      <div style={{ background:'linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#1e1b4b 100%)', border:'2px solid #818cf8', borderRadius:'12px', padding: isMobile ? '16px 14px' : '24px 28px', marginBottom:'24px', color:'white' }}>
        <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1.5px', color:'#a5b4fc', marginBottom:'6px' }}>2026 Major Race Calendar</div>
        <div style={{ fontSize: isMobile ? '20px' : '24px', fontWeight:'800', marginBottom:'8px' }}>Group 1 &amp; Feature Races</div>
        <div style={{ fontSize:'14px', color:'rgba(255,255,255,0.75)', marginBottom: nextRace ? '16px' : '0' }}>
          {upcomingCount} upcoming major races \u00b7 UK &amp; Ireland
        </div>
        {nextRace && (
          <div style={{ background:'rgba(255,255,255,0.1)', border:'1px solid rgba(255,255,255,0.2)', borderRadius:'8px', padding: isMobile ? '10px 12px' : '12px 16px', display: isMobile ? 'flex' : 'inline-flex', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? '10px' : '20px', flexWrap:'wrap', alignItems: isMobile ? 'stretch' : 'center' }}>
            <div>
              <div style={{ fontSize:'10px', color:'#a5b4fc', textTransform:'uppercase', letterSpacing:'1px' }}>Next Major Race</div>
              <div style={{ fontSize:'16px', fontWeight:'800', marginTop:'2px' }}>{nextRace.name}</div>
              <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.75)' }}>{nextRace.meeting} \u00b7 {formatDate(nextRace.date)}</div>
            </div>
            <div style={{ background:'#818cf8', borderRadius:'8px', padding: isMobile ? '6px 14px' : '8px 18px', fontSize: isMobile ? '16px' : '20px', fontWeight:'800', minWidth: isMobile ? 'auto' : '100px', textAlign:'center' }}>{daysUntil(nextRace.date)}</div>
          </div>
        )}
      </div>

      <div style={{ display:'flex', gap:'8px', flexWrap:'wrap', marginBottom:'20px', alignItems:'center' }}>
        {[
          { key:'all',       label:'All Races'       },
          { key:'highlight', label:'\u2b50 Highlights' },
          { key:'NH',        label:'National Hunt'   },
          { key:'Flat',      label:'Flat Racing'     },
        ].map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)} style={{
            background: filter===f.key ? 'rgba(129,140,248,0.3)' : 'rgba(255,255,255,0.08)',
            border:     filter===f.key ? '2px solid #818cf8' : '2px solid rgba(255,255,255,0.15)',
            borderRadius:'8px', color:'white', cursor:'pointer', padding:'8px 16px', fontSize:'13px',
            fontWeight: filter===f.key ? '700' : '400', transition:'all 0.15s',
          }}>{f.label}</button>
        ))}
        <button onClick={() => setShowPast(!showPast)} style={{ background: showPast?'rgba(107,114,128,0.3)':'rgba(255,255,255,0.05)', border:'2px solid rgba(255,255,255,0.15)', borderRadius:'8px', color:'rgba(255,255,255,0.6)', cursor:'pointer', padding:'8px 16px', fontSize:'12px', marginLeft:'auto' }}>
          {showPast ? 'Hide Past' : 'Show Past'}
        </button>
      </div>

      {grouped.length === 0 ? (
        <div style={{ textAlign:'center', padding:'48px', color:'rgba(255,255,255,0.5)', fontSize:'16px' }}>No races match the filter.</div>
      ) : grouped.map(({ date, meeting, races }) => {
        const past = isPast(date);
        const col  = meetingColour(meeting);
        return (
          <div key={date + '__' + meeting} style={{ background: past ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.08)', borderRadius:'12px', marginBottom:'20px', overflow:'hidden', opacity: past ? 0.65 : 1 }}>
            <div style={{ background: past ? '#374151' : col, padding: isMobile ? '10px 14px' : '14px 20px', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'8px' }}>
              <div>
                <span style={{ fontSize: isMobile ? '15px' : '18px', fontWeight:'800', color:'white' }}>{meeting}</span>
                <span style={{ fontSize: isMobile ? '12px' : '13px', color:'rgba(255,255,255,0.8)', marginLeft: isMobile ? '8px' : '12px' }}>{formatDate(date)}</span>
              </div>
              {past
                ? <span style={{ background:'rgba(0,0,0,0.25)', color:'white', padding:'4px 12px', borderRadius:'6px', fontSize:'12px', fontWeight:'600' }}>Complete</span>
                : <span style={{ background:'rgba(255,255,255,0.25)', color:'white', padding:'4px 14px', borderRadius:'6px', fontSize:'13px', fontWeight:'800' }}>{daysUntil(date)}</span>
              }
            </div>
            <div style={{ padding: isMobile ? '10px 12px' : '12px 16px', display:'flex', flexDirection:'column', gap:'10px' }}>
              {races.map((race, i) => {
                const raceKey = `${race.date}__${race.name.replace(/ /g, '_')}`;
                const analysis = getSyncedMajorAnalysis(race, analyses[raceKey]);
                const pickMadeAt = formatPickMadeAt(analysis?.analysed_at);
                const isExpanded = expandedRace === raceKey;
                const confColour = { HIGH: '#34d399', MEDIUM: '#fbbf24', LOW: '#f87171', 'NO DATA': 'rgba(255,255,255,0.3)' };
                return (
                <div key={i} style={{
                  background: race.highlight && !past ? 'linear-gradient(135deg,rgba(217,119,6,0.12) 0%,rgba(255,255,255,0.08) 100%)' : 'rgba(255,255,255,0.05)',
                  border:     race.highlight && !past ? '1px solid rgba(217,119,6,0.4)' : '1px solid rgba(255,255,255,0.1)',
                  borderRadius:'8px', padding:'12px 16px',
                }}>
                  <div style={{ display:'flex', alignItems:'flex-start', gap:'8px', flexWrap:'wrap' }}>
                    {race.highlight && !past && <span>\u2b50</span>}
                    <div style={{ flex:1 }}>
                      <div style={{ display:'flex', alignItems:'center', gap:'8px', flexWrap:'wrap', marginBottom:'4px' }}>
                        <span style={{ fontSize:'16px', fontWeight:'700', color:'white' }}>{race.name}</span>
                        <span style={{
                          background: race.grade==='G1' ? 'linear-gradient(135deg,#d97706,#b45309)' : race.grade==='G2' ? '#1d4ed8' : '#374151',
                          color:'white', padding:'2px 8px', borderRadius:'5px', fontSize:'11px', fontWeight:'700',
                        }}>{race.grade}</span>
                        <span style={{
                          background: race.type==='NH' ? 'rgba(4,120,87,0.3)' : 'rgba(29,78,216,0.3)',
                          border: `1px solid ${race.type==='NH' ? '#059669' : '#3b82f6'}`,
                          color:  race.type==='NH' ? '#6ee7b7' : '#93c5fd',
                          padding:'2px 8px', borderRadius:'5px', fontSize:'11px',
                        }}>{race.type==='NH' ? 'Jump' : 'Flat'}</span>
                      </div>
                      <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', display:'flex', gap:'14px', flexWrap:'wrap', marginBottom: race.notes ? '5px' : '0' }}>
                        <span>{race.distance}</span>
                        {race.purse && <span>{race.purse}</span>}
                      </div>
                      {race.notes && <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.65)', lineHeight:'1.5' }}>{race.notes}</div>}

                      {/* ── Early Bird AI Pick ────────────────────────── */}
                      {!past && analysis && analysis.top_pick && (
                        <div style={{ marginTop:'10px', background:'linear-gradient(135deg,rgba(99,102,241,0.12),rgba(129,140,248,0.08))', border:'1px solid rgba(129,140,248,0.3)', borderRadius:'8px', padding:'10px 14px' }}>
                          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'8px' }}>
                            <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                              <span style={{ fontSize:'14px' }}>🐴</span>
                              <div>
                                <div style={{ fontSize:'11px', color:'#a5b4fc', textTransform:'uppercase', letterSpacing:'1px', fontWeight:'700' }}>Early Bird AI Pick</div>
                                <div style={{ fontSize:'15px', fontWeight:'800', color:'white', marginTop:'2px' }}>{analysis.top_pick}
                                  {analysis.top_pick_odds && <span style={{ fontSize:'12px', fontWeight:'600', color:'#a5b4fc', marginLeft:'8px' }}>{analysis.top_pick_odds}</span>}
                                </div>
                                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.55)', marginTop:'3px' }}>
                                  {pickMadeAt ? `Pick made: ${pickMadeAt}` : 'Pick made: timestamp unavailable'}
                                </div>
                              </div>
                            </div>
                            <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                              <span style={{ background: `${confColour[analysis.confidence] || confColour['NO DATA']}22`, border:`1px solid ${confColour[analysis.confidence] || confColour['NO DATA']}55`, color: confColour[analysis.confidence] || confColour['NO DATA'], padding:'3px 10px', borderRadius:'6px', fontSize:'11px', fontWeight:'700' }}>
                                {analysis.confidence}
                              </span>
                              <button onClick={() => setExpandedRace(isExpanded ? null : raceKey)} style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.15)', borderRadius:'6px', color:'rgba(255,255,255,0.6)', fontSize:'11px', padding:'3px 10px', cursor:'pointer' }}>
                                {isExpanded ? '▲ Less' : '▼ More'}
                              </button>
                            </div>
                          </div>
                          {analysis.top_pick_factors && analysis.top_pick_factors.length > 0 && (
                            <div style={{ display:'flex', gap:'6px', flexWrap:'wrap', marginTop:'6px' }}>
                              {analysis.top_pick_factors.slice(0, 3).map((f, fi) => (
                                <span key={fi} style={{ background:'rgba(129,140,248,0.15)', border:'1px solid rgba(129,140,248,0.25)', color:'#c7d2fe', padding:'2px 8px', borderRadius:'4px', fontSize:'10px' }}>{f}</span>
                              ))}
                            </div>
                          )}
                          {isExpanded && analysis.top3 && (
                            <div style={{ marginTop:'10px', borderTop:'1px solid rgba(129,140,248,0.15)', paddingTop:'10px' }}>
                              <div style={{ fontSize:'11px', color:'#a5b4fc', fontWeight:'700', marginBottom:'8px', textTransform:'uppercase', letterSpacing:'0.5px' }}>Top Contenders</div>
                              {analysis.top3.map((h, hi) => (
                                <div key={hi} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'6px 10px', background: hi === 0 ? 'rgba(129,140,248,0.1)' : 'transparent', borderRadius:'6px', marginBottom:'4px' }}>
                                  <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                                    <span style={{ fontSize:'14px', fontWeight:'800', color: hi === 0 ? '#818cf8' : hi === 1 ? '#a5b4fc' : 'rgba(255,255,255,0.4)', width:'20px' }}>{hi + 1}.</span>
                                    <div>
                                      <span style={{ fontSize:'13px', fontWeight:'700', color:'white' }}>{h.name}</span>
                                      {h.trainer && <span style={{ fontSize:'11px', color:'rgba(255,255,255,0.4)', marginLeft:'8px' }}>{h.trainer}</span>}
                                    </div>
                                  </div>
                                  <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                                    {h.odds_display && <span style={{ fontSize:'12px', color:'#a5b4fc', fontWeight:'600' }}>{h.odds_display}</span>}
                                    <div style={{ background:'rgba(129,140,248,0.2)', borderRadius:'4px', padding:'2px 8px', fontSize:'11px', fontWeight:'700', color:'#818cf8', minWidth:'32px', textAlign:'center' }}>{h.score}</div>
                                  </div>
                                </div>
                              ))}
                              {analysis.total_horses > 0 && (
                                <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.3)', marginTop:'6px' }}>
                                  {analysis.total_horses} runners analysed · {pickMadeAt ? `Pick made ${pickMadeAt}` : 'Pick made time unavailable'} · {analysis.days_to_race} days to race
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      {!past && !analysis && !analysisLoading && !isPast(race.date) && daysUntil(race.date) && (
                        <div style={{ marginTop:'8px', fontSize:'11px', color:'rgba(255,255,255,0.3)', fontStyle:'italic' }}>
                          🔮 Early bird analysis coming soon
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
              })}
            </div>
          </div>
        );
      })}

      <div style={{ marginTop:'20px', padding:'14px 18px', background:'rgba(255,255,255,0.06)', borderRadius:'10px', color:'rgba(255,255,255,0.5)', fontSize:'12px', display:'flex', gap:'20px', flexWrap:'wrap', justifyContent:'center' }}>
        <span><span style={{ background:'linear-gradient(135deg,#d97706,#b45309)', color:'white', padding:'1px 7px', borderRadius:'4px', fontSize:'11px', fontWeight:'700', marginRight:'6px' }}>G1</span>Group 1</span>
        <span><span style={{ background:'#1d4ed8', color:'white', padding:'1px 7px', borderRadius:'4px', fontSize:'11px', fontWeight:'700', marginRight:'6px' }}>G2</span>Group 2</span>
        <span>\u2b50 Must-watch highlight races</span>
        <span>Dates are indicative and may change</span>
      </div>
      <LegalDisclaimerCard />
    </div>
  );
}

// ---- Lay the Fav View ----
function LayTheFavView() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const [filter, setFilter] = useState('all'); // all | caution | strong
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE_URL}/api/favs-run`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const VERDICT_COLOURS = {
    RED:    { fg:'#f87171', bg:'rgba(248,113,113,0.12)', border:'rgba(248,113,113,0.35)' },
    AMBER:  { fg:'#f97316', bg:'rgba(249,115,22,0.12)',  border:'rgba(249,115,22,0.35)'  },
    YELLOW: { fg:'#fbbf24', bg:'rgba(251,191,36,0.10)',  border:'rgba(251,191,36,0.35)'  },
    GREEN:  { fg:'#34d399', bg:'rgba(52,211,153,0.10)',  border:'rgba(52,211,153,0.3)'   },
  };

  if (loading) return (
    <div style={{ textAlign:'center', padding:'60px', color:'rgba(255,255,255,0.5)' }}>
      <div style={{ fontSize:'32px', marginBottom:'12px' }}>🚨</div>
      <div>Loading lay analysis…</div>
    </div>
  );

  if (error || !data?.success) return (
    <div style={{ textAlign:'center', padding:'60px', color:'#f87171' }}>
      <div style={{ fontSize:'28px', marginBottom:'12px' }}>⚠️</div>
      <div>{error || data?.error || 'Failed to load'}</div>
    </div>
  );

  const { summary, races, generated, history_days, history_summary } = data;
  const genTime = generated ? new Date(generated).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'}) : '';
  const dailyHistory = Array.isArray(history_days) ? history_days : [];
  const historyAgg = history_summary || {};

  const nowUtc = new Date();
  const isPast = r => {
    if (!r.race_time) return false;
    try { return new Date(r.race_time) < nowUtc; } catch { return false; }
  };

  const layScore = r => parseFloat(r.lay_score || 0);
  const displayRaces = races.filter(r => layScore(r) >= 4);
  const settledDisplayRaces = displayRaces.filter(isPast);
  const settledResolved = settledDisplayRaces.filter(r => r.outcome && ['win', 'won', 'loss', 'lost'].includes(String(r.outcome).toLowerCase()));
  const favLostCount = settledResolved.filter(r => !['win', 'won'].includes(String(r.outcome).toLowerCase())).length;
  const layWinPct = settledResolved.length ? Math.round((favLostCount / settledResolved.length) * 100) : null;
  const displaySummary = {
    total: settledDisplayRaces.length,
    caution: settledDisplayRaces.length,
    strong: settledDisplayRaces.filter(r => layScore(r) >= 7).length,
    red_flag: settledDisplayRaces.filter(r => layScore(r) >= 10).length,
    fav_lost: favLostCount,
    settled: settledResolved.length,
    lay_win_pct: layWinPct,
  };

  // Cards: only show races score 4+ (0-3 are too weak to display)
  const filtered = displayRaces.filter(r =>
    isPast(r) && (
      filter === 'red'     ? layScore(r) >= 10 :
      filter === 'strong'  ? layScore(r) >= 7 :
      true
    )
  );

  const downloadLaySelectionsCsv = () => {
    const btn = document.getElementById('vip-lay-selections-download-btn');
    if (btn) btn.textContent = 'Downloading...';

    const csvEndpoint = data?.csv_url
      ? `${API_BASE_URL}${data.csv_url}`
      : `${API_BASE_URL}/api/favs-run?days=1&format=csv`;

    fetch(csvEndpoint)
      .then(r => {
        if (!r.ok) throw new Error('CSV download failed');
        return r.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'VIP_Rollers_Lay_Selections.csv';
        a.click();
        URL.revokeObjectURL(url);
        if (btn) btn.textContent = 'Downloaded';
        setTimeout(() => { if (btn) btn.textContent = 'Download Lay Selections CSV'; }, 2500);
      })
      .catch(() => {
        if (btn) btn.textContent = 'Download Failed';
        setTimeout(() => { if (btn) btn.textContent = 'Download Lay Selections CSV'; }, 2500);
      });
  };

  return (
    <div style={{ paddingBottom:'40px' }}>

      {/* Header */}
      <div style={{ background:'linear-gradient(135deg,rgba(217,119,6,0.25) 0%,rgba(180,83,9,0.18) 100%)', border:'1px solid rgba(245,158,11,0.3)', borderRadius:'14px', padding: isMobile ? '16px 14px' : '24px 28px', marginBottom:'24px' }}>
        <div style={{ fontSize:'11px', letterSpacing:'2px', textTransform:'uppercase', color:'rgba(255,255,255,0.4)', marginBottom:'6px' }}>VIP Rollers · Lay Vulnerable Favorites</div>
        <div style={{ fontSize:'22px', fontWeight:'800', color:'white', marginBottom:'4px' }}>👑 VIP Rollers — Lay Vulnerable Favorites</div>
        <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)', marginBottom:'12px' }}>Highlights vulnerable favorites to avoid backing and potential lay opportunities on exchange markets.</div>

        {/* Exchange account notice */}
        <div style={{ display:'flex', alignItems:'flex-start', gap:'10px', background:'rgba(251,191,36,0.08)', border:'1px solid rgba(251,191,36,0.25)', borderRadius:'10px', padding:'12px 16px', marginBottom:'18px' }}>
          <span style={{ fontSize:'18px', flexShrink:0 }}>🔄</span>
          <div>
            <div style={{ fontSize:'13px', fontWeight:'700', color:'#fbbf24', marginBottom:'2px' }}>Bet Exchange Account Required</div>
            <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', lineHeight:'1.5' }}>VIP Rollers is built around <strong style={{ color:'rgba(255,255,255,0.8)' }}>laying horses on the exchange</strong>, using a specialist strategy designed to profit when selections lose. You'll need an account with Betfair Exchange or similar to place lay bets.</div>
          </div>
        </div>

        {/* Score legend */}
        <div style={{ display:'flex', gap:'10px', flexWrap:'wrap', marginBottom:'18px' }}>
          {[{score:'4-6', label:'Possible Lay', c:'#fbbf24'}, {score:'7-9', label:'Strong Lay', c:'#f97316'}, {score:'10+', label:'Premium Lay', c:'#f87171'}].map(l => (
            <div key={l.score} style={{ display:'flex', alignItems:'center', gap:'6px', background:'rgba(255,255,255,0.06)', borderRadius:'8px', padding:'5px 12px', fontSize:'12px', color:'rgba(255,255,255,0.7)' }}>
              <span style={{ background:l.c, width:'8px', height:'8px', borderRadius:'50%', display:'inline-block' }} />
              <b style={{ color:l.c }}>{l.score}</b>&nbsp;{l.label}
            </div>
          ))}
        </div>

        {/* Stats */}
        <div style={{ display:'grid', gridTemplateColumns: isMobile ? 'repeat(2,1fr)' : 'repeat(auto-fill,minmax(120px,1fr))', gap:'10px', flexWrap:'wrap' }}>
          {[{v:displaySummary.total, lbl:'Analysed (4+)', c:'#94a3b8'}, {v:displaySummary.caution, lbl:'Possible Lay (4+)', c:'#fbbf24'}, {v:displaySummary.strong, lbl:'Strong Lay (7+)', c:'#f97316'}, {v:displaySummary.red_flag, lbl:'Premium Lay (10+)', c:'#f87171'},
            {v: displaySummary.lay_win_pct != null ? `${displaySummary.lay_win_pct}%` : '—', lbl:`Lay Win % (${displaySummary.fav_lost}/${displaySummary.settled})`, c:'#22d3ee'}].map(s => (
            <div key={s.lbl} style={{ background:'rgba(255,255,255,0.07)', borderRadius:'10px', padding:'10px 18px', textAlign:'center' }}>
              <div style={{ fontSize:'24px', fontWeight:'800', color:s.c }}>{s.v}</div>
              <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.5)', marginTop:'2px' }}>{s.lbl}</div>
            </div>
          ))}
          {genTime && <div style={{ marginLeft:'auto', fontSize:'11px', color:'rgba(255,255,255,0.35)', alignSelf:'flex-end', paddingBottom:'4px' }}>Updated {genTime}</div>}
        </div>
      </div>

      {/* Rolling history */}
      {dailyHistory.length > 0 && (
        <div style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(34,211,238,0.28)', borderRadius:'12px', padding: isMobile ? '12px' : '14px 18px', marginBottom:'14px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', gap:'10px', flexWrap:'wrap', marginBottom:'10px' }}>
            <div style={{ fontSize:'12px', fontWeight:'800', letterSpacing:'0.8px', textTransform:'uppercase', color:'#67e8f9' }}>Rolling Lay History</div>
            <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.6)' }}>
              {historyAgg.days || dailyHistory.length} days · {historyAgg.settled || 0} settled · {historyAgg.fav_lost || 0} fav lost · {historyAgg.lay_win_pct != null ? `${historyAgg.lay_win_pct}%` : '—'} lay win
            </div>
          </div>
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ borderBottom:'1px solid rgba(255,255,255,0.15)' }}>
                  {['Date', 'Total', 'Settled', 'Fav Lost', 'Lay Win %'].map(h => (
                    <th key={h} style={{ textAlign:'left', padding:'6px 8px', fontSize:'11px', color:'rgba(255,255,255,0.5)', textTransform:'uppercase', letterSpacing:'0.7px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dailyHistory.slice(0, 14).map((day, idx) => {
                  const s = day.summary || {};
                  return (
                    <tr key={`${day.date}-${idx}`} style={{ borderBottom:'1px solid rgba(255,255,255,0.08)' }}>
                      <td style={{ padding:'6px 8px', fontSize:'12px', color:'white' }}>{day.date || '-'}</td>
                      <td style={{ padding:'6px 8px', fontSize:'12px', color:'rgba(255,255,255,0.8)' }}>{s.total || 0}</td>
                      <td style={{ padding:'6px 8px', fontSize:'12px', color:'rgba(255,255,255,0.8)' }}>{s.settled || 0}</td>
                      <td style={{ padding:'6px 8px', fontSize:'12px', color:'#34d399' }}>{s.fav_lost || 0}</td>
                      <td style={{ padding:'6px 8px', fontSize:'12px', color:'#22d3ee', fontWeight:'700' }}>{s.lay_win_pct != null ? `${s.lay_win_pct}%` : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Filter buttons */}
      <div style={{ display:'flex', gap:'8px', marginBottom:'16px', flexWrap:'wrap' }}>
        {[{k:'all',label:'All'},{ k:'caution',label:'Possible Lay (4+)'},{ k:'strong',label:'Strong Lay (7+)'},{ k:'red',label:'Premium Lay (10+)'}].map(f => (
          <button key={f.k} onClick={() => setFilter(f.k)} style={{
            background: filter===f.k ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.07)',
            border: filter===f.k ? '1px solid #f87171' : '1px solid rgba(255,255,255,0.15)',
            borderRadius:'6px', color:'white', cursor:'pointer', padding:'6px 14px', fontSize:'12px', fontWeight: filter===f.k ? '700' : '400',
          }}>{f.label}</button>
        ))}
        <button
          onClick={downloadLaySelectionsCsv}
          id="vip-lay-selections-download-btn"
          style={{
            background:'rgba(249,115,22,0.16)',
            border:'1px solid rgba(249,115,22,0.48)',
            borderRadius:'6px',
            color:'#fdba74',
            cursor:'pointer',
            padding:'6px 12px',
            fontSize:'12px',
            fontWeight:'700'
          }}
        >Download Lay Selections CSV</button>
        <button
          onClick={() => {
            const btn = document.getElementById('vip-historical-download-btn');
            if (btn) btn.textContent = 'Downloading...';
            if (dailyHistory.length > 0) {
              const rows = [['date','total','settled','fav_lost','lay_win_pct']];
              dailyHistory.forEach(day => {
                const s = day.summary || {};
                rows.push([
                  day.date || '',
                  s.total || 0,
                  s.settled || 0,
                  s.fav_lost || 0,
                  s.lay_win_pct != null ? s.lay_win_pct : ''
                ]);
              });
              const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n');
              const blob = new Blob([csv], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'VIP_Rollers_Lay_History.csv';
              a.click();
              URL.revokeObjectURL(url);
              if (btn) btn.textContent = 'Downloaded';
              setTimeout(() => { if (btn) btn.textContent = 'Download Historical Results'; }, 2500);
              return;
            }

            fetch(API_BASE_URL + '/api/results/export-csv')
              .then(r => r.text())
              .then(csv => {
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'VIP_Rollers_Historical_Results.csv';
                a.click();
                URL.revokeObjectURL(url);
                if (btn) btn.textContent = 'Downloaded';
                setTimeout(() => { if (btn) btn.textContent = 'Download Historical Results'; }, 2500);
              })
              .catch(() => {
                if (btn) btn.textContent = 'Download Failed';
                setTimeout(() => { if (btn) btn.textContent = 'Download Historical Results'; }, 2500);
              });
          }}
          id="vip-historical-download-btn"
          style={{
            background:'rgba(34,211,238,0.14)',
            border:'1px solid rgba(34,211,238,0.45)',
            borderRadius:'6px',
            color:'#67e8f9',
            cursor:'pointer',
            padding:'6px 12px',
            fontSize:'12px',
            fontWeight:'700'
          }}
        >Download Historical Results</button>
        <span style={{ marginLeft:'auto', fontSize:'12px', color:'rgba(255,255,255,0.4)', alignSelf:'center' }}>{filtered.length} settled race{filtered.length!==1?'s':''} · {displayRaces.filter(r => !isPast(r)).length} pending</span>
      </div>

      {/* Race cards */}
      {filtered.length === 0 && (
        <div style={{ textAlign:'center', padding:'40px', color:'rgba(255,255,255,0.4)', background:'rgba(255,255,255,0.04)', borderRadius:'10px' }}>
          {settledDisplayRaces.length === 0 ? 'No races have started yet — results will appear here as races settle.' : 'No settled races match this filter.'}
        </div>
      )}

      {filtered.map((r, i) => {
        const vc = VERDICT_COLOURS[r.verdict_colour] || VERDICT_COLOURS.GREEN;
        const barPct = Math.min(100, Math.round(r.lay_score / 35 * 100));
        return (
          <div key={i} style={{ background:'rgba(22,27,34,0.95)', border:`1px solid ${vc.border}`, borderLeft:`4px solid ${vc.fg}`, borderRadius:'10px', marginBottom:'14px', overflow:'hidden' }}>

            {/* Card header */}
            <div style={{ display:'flex', alignItems:'center', gap: isMobile ? '6px' : '10px', flexWrap:'wrap', padding: isMobile ? '10px 12px' : '12px 18px', borderBottom:'1px solid rgba(255,255,255,0.07)', background:'rgba(255,255,255,0.02)' }}>
              <span style={{ fontWeight:'800', color:'#58a6ff', fontSize: isMobile ? '13px' : '15px', minWidth:'40px' }}>{fmtUtcTime(r.race_time)}</span>
              <span style={{ fontWeight:'700', color:'white', fontSize: isMobile ? '13px' : '14px' }}>{r.course}</span>
              <span style={{ flex:1, fontSize:'12px', color:'rgba(255,255,255,0.45)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace: isMobile ? 'normal' : 'nowrap', minWidth:0 }}>{r.race_name}</span>
              {r.our_pick && <span style={{ background:'rgba(88,166,255,0.18)', color:'#58a6ff', border:'1px solid rgba(88,166,255,0.4)', borderRadius:'4px', padding:'2px 8px', fontSize:'11px', fontWeight:'700' }}>⚡ OUR PICK</span>}
              {r.outcome && ['win','won','loss','lost'].includes(r.outcome.toLowerCase()) && (() => {
                const oc = r.outcome.toLowerCase();
                const favWon = ['win','won'].includes(oc);
                return (
                  <span style={{
                    background: favWon ? 'rgba(248,113,113,0.18)' : 'rgba(52,211,153,0.18)',
                    color:       favWon ? '#f87171' : '#34d399',
                    border:      `1px solid ${favWon ? 'rgba(248,113,113,0.5)' : 'rgba(52,211,153,0.5)'}`,
                    borderRadius:'4px', padding:'2px 10px', fontSize:'11px', fontWeight:'800',
                    whiteSpace:'nowrap', letterSpacing:'0.3px',
                  }}>
                    {favWon ? '✗ FAV WON' : '✓ FAV LOST'}
                  </span>
                );
              })()}
              <span style={{ background:vc.bg, color:vc.fg, border:`1px solid ${vc.border}`, borderRadius:'5px', padding:'2px 10px', fontSize:'11px', fontWeight:'700', textTransform:'uppercase', letterSpacing:'0.5px', whiteSpace:'nowrap' }}>{r.verdict}</span>
            </div>

            {/* Card body */}
            <div style={{ display:'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: isMobile ? '12px' : '20px', padding: isMobile ? '12px 14px' : '14px 18px' }}>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:'20px', fontWeight:'800', color:'white', marginBottom:'6px' }}>{r.favourite}</div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:'4px 16px', fontSize:'12px', color:'rgba(255,255,255,0.5)', marginBottom:'4px', alignItems:'center' }}>
                  <span>@ <b style={{color:'#e6edf3'}}>{r.fav_odds?.toFixed(2)}</b></span>
                  {r.fav_odds <= 1.7 && (
                    <span style={{ background:'#7c2d12', color:'#fca5a5', border:'1px solid #f87171', borderRadius:'4px', padding:'1px 7px', fontSize:'11px', fontWeight:'700' }}>⚠ Extreme Fav — Check N/R</span>
                  )}
                  <span>Form <b style={{color:'#e6edf3'}}>{r.form || '—'}</b></span>
                  <span>Runners <b style={{color:'#e6edf3'}}>{r.runners}</b></span>
                </div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:'4px 16px', fontSize:'12px', color:'rgba(255,255,255,0.5)' }}>
                  <span>Trainer <b style={{color:'rgba(255,255,255,0.75)'}}>{r.trainer || '—'}</b></span>
                  <span>Jockey <b style={{color:'rgba(255,255,255,0.75)'}}>{r.jockey || '—'}</b></span>
                </div>
              </div>

              {/* Score circle */}
              <div style={{ textAlign: isMobile ? 'left' : 'center', minWidth: isMobile ? 'auto' : '72px', display: isMobile ? 'flex' : 'block', alignItems:'center', gap:'10px' }}>
                <div style={{ fontSize: isMobile ? '28px' : '38px', fontWeight:'800', lineHeight:1, color:vc.fg }}>{r.lay_score}</div>
                <div style={{ display: isMobile ? 'none' : 'block', fontSize:'11px', color:'rgba(255,255,255,0.4)', marginBottom:'6px' }}>/ 35</div>
                <div style={{ width:'64px', height:'6px', background:'rgba(255,255,255,0.1)', borderRadius:'3px', overflow:'hidden', margin: isMobile ? '0' : '0 auto' }}>
                  <div style={{ width:`${barPct}%`, height:'100%', background:vc.fg, borderRadius:'3px' }} />
                </div>
              </div>
            </div>

          </div>
        );
      })}

      {/* Summary table */}
      {displayRaces.length > 0 && (
        <div style={{ marginTop:'24px' }}>
          <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.35)', marginBottom:'10px' }}>Summary Table</div>
          {isMobile ? (
            /* Mobile: card layout */
            <div style={{ display:'flex', flexDirection:'column', gap:'8px' }}>
              {[...displayRaces].sort((a,b) => (a.race_time||'') < (b.race_time||'') ? -1 : 1).map((r, i) => {
                const vc = VERDICT_COLOURS[r.verdict_colour] || VERDICT_COLOURS.GREEN;
                const past = isPast(r);
                const favWon = past && r.outcome && ['win','won'].includes(r.outcome.toLowerCase());
                const favLost = past && r.outcome && !['win','won'].includes(r.outcome.toLowerCase());
                return (
                  <div key={i} style={{ background:'rgba(22,27,34,0.95)', border:'1px solid rgba(255,255,255,0.1)', borderLeft:`3px solid ${vc.fg}`, borderRadius:'8px', padding:'10px 12px', opacity: past ? 1 : 0.5 }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'6px' }}>
                      <span style={{ fontSize:'13px', color:'#58a6ff', fontWeight:'700' }}>{fmtUtcTime(r.race_time)}</span>
                      <span style={{ fontSize:'12px', color:'rgba(255,255,255,0.8)' }}>{r.course}</span>
                      <span style={{ fontSize:'14px', fontWeight:'800', color:vc.fg }}>{r.lay_score}</span>
                    </div>
                    <div style={{ fontSize:'13px', color:'white', fontWeight:'600', marginBottom:'4px' }}>{r.favourite} <span style={{ color:'rgba(255,255,255,0.5)', fontWeight:'400' }}>@ {r.fav_odds?.toFixed(2)}</span></div>
                    <div style={{ display:'flex', gap:'6px', alignItems:'center', flexWrap:'wrap' }}>
                      <span style={{ background:vc.bg, color:vc.fg, border:`1px solid ${vc.border}`, borderRadius:'4px', padding:'2px 8px', fontSize:'11px', fontWeight:'700' }}>{r.verdict}</span>
                      {!past
                        ? <span style={{ color:'rgba(255,255,255,0.25)', fontSize:'11px' }}>⏳ Pending</span>
                        : favLost
                          ? <span style={{ color:'#34d399', fontWeight:'800', fontSize:'11px' }}>✓ FAV LOST</span>
                          : favWon
                            ? <span style={{ color:'#f87171', fontWeight:'800', fontSize:'11px' }}>✗ FAV WON</span>
                            : <span style={{ color:'rgba(255,255,255,0.25)', fontSize:'11px' }}>—</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', background:'rgba(22,27,34,0.95)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px', overflow:'hidden' }}>
              <thead>
                <tr style={{ background:'rgba(255,255,255,0.06)' }}>
                  {['Time','Course','Favourite','Odds','Lay Score','Verdict','Result'].map(h => (
                    <th key={h} style={{ padding:'9px 12px', fontSize:'11px', textTransform:'uppercase', letterSpacing:'0.7px', color:'rgba(255,255,255,0.4)', textAlign:'left', borderBottom:'1px solid rgba(255,255,255,0.1)', whiteSpace:'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...displayRaces].sort((a,b) => (a.race_time||'') < (b.race_time||'') ? -1 : 1).map((r, i) => {
                  const vc = VERDICT_COLOURS[r.verdict_colour] || VERDICT_COLOURS.GREEN;
                  const past = isPast(r);
                  const favWon = past && r.outcome && ['win','won'].includes(r.outcome.toLowerCase());
                  const favLost = past && r.outcome && !['win','won'].includes(r.outcome.toLowerCase());
                  return (
                    <tr key={i} style={{ borderBottom:'1px solid rgba(255,255,255,0.06)', opacity: past ? 1 : 0.5 }}>
                      <td style={{ padding:'9px 12px', fontSize:'13px', color:'#58a6ff', fontWeight:'700' }}>{fmtUtcTime(r.race_time)}</td>
                      <td style={{ padding:'9px 12px', fontSize:'13px', color:'rgba(255,255,255,0.8)' }}>{r.course}</td>
                      <td style={{ padding:'9px 12px', fontSize:'13px', color:'white', fontWeight:'600' }}>{r.favourite}</td>
                      <td style={{ padding:'9px 12px', fontSize:'13px', color:'rgba(255,255,255,0.7)' }}>{r.fav_odds?.toFixed(2)}</td>
                      <td style={{ padding:'9px 12px', fontSize:'14px', fontWeight:'800', color:vc.fg }}>{r.lay_score}</td>
                      <td style={{ padding:'9px 12px' }}><span style={{ background:vc.bg, color:vc.fg, border:`1px solid ${vc.border}`, borderRadius:'4px', padding:'2px 8px', fontSize:'11px', fontWeight:'700' }}>{r.verdict}</span></td>
                      <td style={{ padding:'9px 12px' }}>
                        {!past
                          ? <span style={{ color:'rgba(255,255,255,0.25)', fontSize:'12px' }}>⏳ Pending</span>
                          : favLost
                            ? <span style={{ color:'#34d399', fontWeight:'800', fontSize:'12px' }}>✓ FAV LOST</span>
                            : favWon
                              ? <span style={{ color:'#f87171', fontWeight:'800', fontSize:'12px' }}>✗ FAV WON</span>
                              : <span style={{ color:'rgba(255,255,255,0.25)', fontSize:'12px' }}>—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          )}
        </div>
      )}
      <LegalDisclaimerCard />
    </div>
  );
}

function HomePageView({ onAuthSuccess, isAuthenticated, authUser, accountSettingsRequest }) {
  const [roi, setRoi]         = useState(null);
  const [settled, setSettled] = useState(null);
  const [roiLoading, setRoiLoading] = useState(true);
  const [latestWinner, setLatestWinner] = useState(null);
  const [yesterdaySummary, setYesterdaySummary] = useState(null);
  const [yesterdayPicks, setYesterdayPicks] = useState([]);
  const [yesterdayDate, setYesterdayDate] = useState('');
  const [preSignPickCount, setPreSignPickCount] = useState(6);
  const [authMode, setAuthMode] = useState('login'); // 'register' | 'login' | 'forgot' | 'reset'
  const [selectedTrialTier, setSelectedTrialTier] = useState('premium');
  const [featuredSnapshot, setFeaturedSnapshot] = useState(null);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768);

  const [form, setForm] = useState({
    fullName: '', email: '', age: '',
    username: '', password: '', confirmPassword: '', agreeTerms: false,
  });
  const [formState, setFormState] = useState('idle');
  const [formError, setFormError] = useState('');

  const [loginForm, setLoginForm] = useState({ emailOrUser: '', password: '' });
  const [loginState, setLoginState] = useState('idle');
  const [loginError, setLoginError] = useState('');

  // ── Forgot / Reset password state ──────────────────────────────────────
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotState, setForgotState] = useState('idle'); // idle | loading | sent | error
  const [forgotError, setForgotError] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetForm, setResetForm] = useState({ password: '', confirmPassword: '' });
  const [resetState, setResetState] = useState('idle'); // idle | loading | success | error
  const [resetError, setResetError] = useState('');

  useEffect(() => {
    if (accountSettingsRequest) setAuthMode('login');
  }, [accountSettingsRequest]);

  // ── Handle ?reset=TOKEN URL param ──────────────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('reset');
    if (token) {
      setResetToken(token);
      setAuthMode('reset');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const handleForgotSubmit = async e => {
    e.preventDefault();
    setForgotError('');
    if (!forgotEmail.trim()) return setForgotError('Please enter your email address.');
    setForgotState('loading');
    try {
      const res = await fetch(`${API_BASE_URL}/api/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail.trim().toLowerCase() }),
      });
      const data = await res.json();
      if (data.success) {
        setForgotState('sent');
      } else {
        setForgotError(data.error || 'Something went wrong. Please try again.');
        setForgotState('error');
      }
    } catch {
      setForgotError('Network error. Please try again.');
      setForgotState('error');
    }
  };

  const handleResetSubmit = async e => {
    e.preventDefault();
    setResetError('');
    if (!resetForm.password || resetForm.password.length < 8) return setResetError('Password must be at least 8 characters.');
    if (resetForm.password !== resetForm.confirmPassword) return setResetError('Passwords do not match.');
    setResetState('loading');
    try {
      const res = await fetch(`${API_BASE_URL}/api/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: resetToken, password: resetForm.password }),
      });
      const data = await res.json();
      if (data.success) {
        setResetState('success');
      } else {
        setResetError(data.error || 'Reset failed. The link may have expired.');
        setResetState('error');
      }
    } catch {
      setResetError('Network error. Please try again.');
      setResetState('error');
    }
  };

  useEffect(() => {
    const todayDate = new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
    const yesterdayDateObj = new Date(`${todayDate}T12:00:00`);
    yesterdayDateObj.setDate(yesterdayDateObj.getDate() - 1);
    const yesterdayDateStr = yesterdayDateObj.toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });

    Promise.all([
      fetch(`${API_BASE_URL}/api/results/cumulative-roi`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/results/latest-winner`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/results/today`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/results/yesterday`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/picks/featured-meeting?date=${yesterdayDateStr}`).then(r => r.json()).catch(() => null),
    ])
      .then(([roiData, latestData, todayData, yesterdayData, featuredData]) => {
        if (roiData?.success) { setRoi(roiData.roi); setSettled(roiData.settled); }
        if (latestData?.success && latestData.fractional_odds) setLatestWinner(latestData);
        if (todayData?.success) {
          const official = Array.isArray(todayData.picks) ? todayData.picks.filter(p => p.show_in_ui !== false).length : 0;
          const watch = Array.isArray(todayData.watchlist) ? todayData.watchlist.length : 0;
          const total = official + watch;
          if (total > 0) setPreSignPickCount(total);
        }
        if (yesterdayData?.success) {
          setYesterdaySummary(yesterdayData.summary || null);
          setYesterdayPicks(Array.isArray(yesterdayData.picks) ? yesterdayData.picks : []);
          setYesterdayDate(yesterdayData.date || '');
        }
        if (featuredData?.success && featuredData.races && featuredData.races.length > 0) {
          // Build featured snapshot - need to check individual race runners
          const featuredRaces = featuredData.races || [];
          const toFrac = (d) => { if (!d || d <= 1) return String(d); const n = Math.round((d - 1) * 4); const den = 4; const gcd = (a, b) => b === 0 ? a : gcd(b, a % b); const g = gcd(n, den); return `${n/g}/${den/g}`; };

          // Find winning picks from race runners
          const winningPicks = [];
          const placedPicks = [];
          let totalSettled = 0;

          for (const race of featuredRaces) {
            if (race.runners && Array.isArray(race.runners)) {
              for (const runner of race.runners) {
                if (runner.rank === 1 && runner.outcome) { // This is our pick
                  totalSettled++;
                  if (runner.outcome.toLowerCase() === 'win') {
                    winningPicks.push({ ...runner, race_time: race.time_user, course: race.course });
                  } else if (runner.outcome.toLowerCase() === 'placed') {
                    placedPicks.push({ ...runner, race_time: race.time_user, course: race.course });
                  }
                  break; // Only one pick per race
                }
              }
            }
          }

          // Get best winner by odds
          const bestWinner = winningPicks.length > 0
            ? winningPicks.reduce((max, r) => (r.odds || 0) > (max.odds || 0) ? r : max, winningPicks[0])
            : null;

          // Always show snapshot if there are results
          if (totalSettled > 0 && bestWinner) {
            setFeaturedSnapshot({
              horse: bestWinner.horse,
              odds: toFrac(bestWinner.odds),
              isWinner: true,
              winners: winningPicks.length,
              placed: placedPicks.length,
              total: totalSettled,
              course: featuredData.course || 'Featured Meet',
              date: featuredData.date || yesterdayDateStr
            });
          }
        }
      })
      .finally(() => setRoiLoading(false));
  }, []);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const selectedTrialLabel = selectedTrialTier === 'vip' ? 'VIP Rollers' : 'Premium';
  const selectedTrialPrice = selectedTrialTier === 'vip' ? '€49.99' : '€9.99';

  const handleSubmit = async e => {
    e.preventDefault();
    setFormError('');
    if (!form.fullName.trim() || form.fullName.trim().length < 3)
      return setFormError('Please enter your full name.');

    // ── Email quality checks ──────────────────────────────────────────
    const emailVal = form.email.trim().toLowerCase();
    const emailRe  = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
    if (!emailRe.test(emailVal))
      return setFormError('Please enter a valid email address (e.g. jane@example.com).');
    if (/\.\../.test(emailVal))
      return setFormError('Email address contains invalid consecutive dots.');
    const emailDomain = emailVal.split('@')[1] || '';
    const emailLocal  = emailVal.split('@')[0] || '';
    if (emailDomain.split('.').pop().length < 2)
      return setFormError('Please enter a valid email address — the domain extension looks incorrect.');
    const garbageEmail = /^(test|asdf|qwerty|aaaaa|zzzzz|abcde|12345|noreply|fake|spam|none|null|xxx)[^@]*$/.test(emailLocal);
    if (garbageEmail)
      return setFormError('Please enter a real email address you have access to.');
    const fakeDomains = ['test.com','fake.com','example.com','mailinator.com','guerrillamail.com','throwam.com','trashmail.com','yopmail.com','sharklasers.com'];
    if (fakeDomains.includes(emailDomain))
      return setFormError('Please use a real email address — disposable/test addresses are not accepted.');

    const age = parseInt(form.age, 10);
    if (isNaN(age) || age < 18 || age > 120)
      return setFormError('You must be 18 or over to register.');
    if (!/^[a-zA-Z0-9_]{3,30}$/.test(form.username))
      return setFormError('Username can only contain letters, numbers and underscores — no spaces or special characters (e.g. Henrik0707 or punter_99).');
    if (form.password.length < 8)
      return setFormError('Password must be at least 8 characters.');
    if (form.password !== form.confirmPassword)
      return setFormError('Passwords do not match.');
    if (!form.agreeTerms)
      return setFormError('You must agree to the Terms & Conditions to register.');

    trackEvent('signup_click', {
      location: 'register_form',
      tier: `${selectedTrialTier}_trial`,
      user_status: 'guest',
    });

    setFormState('loading');
    try {
      const res  = await fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: form.fullName.trim(),
          email:     form.email.trim().toLowerCase(),
          age:       age,
          username:  form.username.trim(),
          password:  form.password,
          desired_tier: selectedTrialTier,
        }),
      });
      const data = await res.json();
      if (data.success) {
        // If backend returned a Stripe checkout URL (7-day trial), redirect there
        if (data.checkout_url) {
          trackEvent('begin_checkout', {
            location: 'register_form',
            tier: `${selectedTrialTier}_trial`,
            user_status: 'guest',
          });
          setFormState('redirecting');
          if (onAuthSuccess) onAuthSuccess(data.user || { email: form.email.trim().toLowerCase(), username: form.username.trim(), full_name: form.fullName.trim() });
          window.location.href = data.checkout_url;
          return;
        }
        setFormState('success');
        if (onAuthSuccess) {
          setTimeout(() => onAuthSuccess(data.user || { email: form.email.trim().toLowerCase(), username: form.username.trim(), full_name: form.fullName.trim() }), 900);
        }
      } else {
        setFormError(data.error || 'Registration failed. Please try again.');
        setFormState('idle');
      }
    } catch {
      setFormError('Network error. Please try again.');
      setFormState('idle');
    }
  };

  const handleLoginChange = e => {
    const { name, value } = e.target;
    setLoginForm(prev => ({ ...prev, [name]: value }));
  };

  const handleLoginSubmit = async e => {
    e.preventDefault();
    setLoginError('');
    if (!loginForm.emailOrUser.trim()) return setLoginError('Please enter your email or username.');
    if (!loginForm.password) return setLoginError('Please enter your password.');
    setLoginState('loading');
    try {
      const res = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginForm.emailOrUser.trim().toLowerCase(), password: loginForm.password }),
      });
      const data = await res.json();
      if (data.success) {
        // If user hasn't completed Stripe checkout, redirect them before granting access
        if (data.checkout_url) {
          trackEvent('begin_checkout', {
            location: 'login_redirect',
            tier: 'premium_trial',
            user_status: 'authenticated',
          });
          setLoginState('idle');
          if (onAuthSuccess) onAuthSuccess(data.user);
          window.location.href = data.checkout_url;
          return;
        }
        if (onAuthSuccess) onAuthSuccess(data.user);
      } else {
        if (data.checkout_url) {
          trackEvent('begin_checkout', {
            location: 'login_redirect',
            tier: 'premium_trial',
            user_status: 'guest',
          });
          setLoginState('idle');
          window.location.href = data.checkout_url;
          return;
        }
        setLoginError(data.error || 'Invalid email/username or password.');
        setLoginState('idle');
      }
    } catch {
      setLoginError('Network error. Please try again.');
      setLoginState('idle');
    }
  };

  const inputStyle = {
    width: '100%', background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.18)',
    borderRadius: '8px', color: 'white', padding: '11px 14px', fontSize: '14px',
    outline: 'none', boxSizing: 'border-box',
  };
  const labelStyle = { display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.55)', marginBottom: '5px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' };
  const fieldStyle = { display: 'flex', flexDirection: 'column', gap: '0' };
  const homeBannerData = buildPositiveBannerData(latestWinner, yesterdaySummary, yesterdayPicks, yesterdayDate);

  if (formState === 'redirecting') {
    return (
      <div style={{ textAlign: 'center', padding: '60px 24px' }}>
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>🔒</div>
        <h2 style={{ color: '#34d399', fontSize: '28px', margin: '0 0 12px' }}>Account Created!</h2>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '16px', maxWidth: '480px', margin: '0 auto 32px' }}>
          Redirecting you to Stripe to start your <strong>7-day free trial</strong>...
        </p>
        <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>You won't be charged during the trial. Cancel anytime.</div>
      </div>
    );
  }

  if (formState === 'success') {
    return (
      <div style={{ textAlign: 'center', padding: '60px 24px' }}>
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>🎉</div>
        <h2 style={{ color: '#34d399', fontSize: '28px', margin: '0 0 12px' }}>Welcome to BetBudAI!</h2>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '16px', maxWidth: '480px', margin: '0 auto 32px' }}>
          Your account has been created. You now have access to our AI-powered daily racing picks and live Return on Investment tracker.
        </p>
        <div style={{ background: 'rgba(5,150,105,0.15)', border: '1px solid rgba(52,211,153,0.35)', borderRadius: '12px', padding: '20px 32px', display: 'inline-block' }}>
          <p style={{ color: '#34d399', margin: 0, fontSize: '15px', fontWeight: '600' }}>✓ Account confirmed for <strong>{form.email}</strong></p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>

      {/* ── HERO ──────────────────────────────────────────────────────── */}
      <div style={{ textAlign: 'center', padding: isMobile ? '12px 0 28px' : '20px 0 48px' }}>

        {/* Featured Snapshot - Dynamic Good News Story (REPLACES gold banner) */}
        {featuredSnapshot && featuredSnapshot.horse && (
          <div style={{
            maxWidth: isMobile ? '100%' : '680px',
            margin: '0 auto 24px',
            padding: isMobile ? '20px 16px' : '28px 24px',
            background: 'linear-gradient(135deg, rgba(52,211,153,0.18), rgba(16,185,129,0.12))',
            border: '2px solid rgba(52,211,153,0.4)',
            borderRadius: '16px',
            boxShadow: '0 8px 24px rgba(52,211,153,0.15)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '16px' }}>
              <span style={{
                fontSize: '13px',
                fontWeight: '900',
                color: '#34d399',
                background: 'rgba(5,150,105,0.25)',
                border: '1.5px solid rgba(52,211,153,0.5)',
                padding: '4px 14px',
                borderRadius: '999px',
                letterSpacing: '1.2px',
                textTransform: 'uppercase'
              }}>
                🏆 Featured Snapshot
              </span>
            </div>
            <div style={{ fontSize: isMobile ? '48px' : '64px', textAlign: 'center', marginBottom: '12px' }}>🏇</div>
            <div style={{
              color: 'rgba(255,255,255,0.95)',
              fontSize: isMobile ? '16px' : '18px',
              fontWeight: '600',
              lineHeight: '1.6',
              textAlign: 'center',
              maxWidth: '800px',
              margin: '0 auto'
            }}>
              Best news: <span style={{ color: '#fbbf24', fontWeight: '900' }}>{featuredSnapshot.horse}</span> landed
              {featuredSnapshot.odds && <> at <span style={{ color: '#34d399', fontWeight: '900', fontSize: '16px' }}>{featuredSnapshot.odds}</span></>}
              {' '}on yesterday&apos;s featured card.
              <span style={{ marginLeft: '6px' }}>
                Yesterday (Wed 20 May):{' '}
                <span style={{ color: '#fbbf24', fontWeight: '900' }}>{featuredSnapshot.winners} winner{featuredSnapshot.winners === 1 ? '' : 's'}</span>
                {' & '}
                <span style={{ color: '#60a5fa', fontWeight: '900' }}>{featuredSnapshot.placed} placed</span>
                {` out of ${featuredSnapshot.total}.`}
              </span>
            </div>
            <div style={{ fontSize: isMobile ? '14px' : '16px', textAlign: 'center', marginTop: '16px' }}>🔥</div>
          </div>
        )}

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(5,150,105,0.18)', border: '1px solid rgba(52,211,153,0.35)', borderRadius: '20px', padding: '6px 16px', marginBottom: '24px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399', boxShadow: '0 0 6px #34d399', display: 'inline-block' }}></span>
          <span style={{ color: '#34d399', fontSize: '12px', fontWeight: '700', letterSpacing: '1px', textTransform: 'uppercase' }}>Live System · UK &amp; Ireland Racing</span>
        </div>
        <h2 style={{ fontSize: isMobile ? '26px' : '42px', fontWeight: '900', margin: '0 0 16px', lineHeight: 1.15, color: 'white' }}>
          Stop guessing. Start winning.<br/>
          <span style={{ background: 'linear-gradient(135deg,#34d399,#059669)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Built for winners. Powered by AI.
          </span>
        </h2>
        {/* ── VS comparison banner ── */}
        <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'center', alignItems: 'stretch', gap: '0', maxWidth: '560px', margin: '0 auto 20px', borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
          {/* Them */}
          <div style={{ flex: 1, background: 'rgba(255,255,255,0.04)', padding: isMobile ? '14px 16px' : '18px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', fontWeight: '700', letterSpacing: '1.5px', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: '4px' }}>Best tipsters in the world</div>
            <div style={{ fontSize: isMobile ? '28px' : '42px', fontWeight: '900', color: '#fbbf24', lineHeight: 1 }}>+10%</div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '3px' }}>Industry benchmark</div>
          </div>
          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.06)', padding: isMobile ? '6px 0' : '0 14px' }}>
            <span style={{ fontSize: '14px', fontWeight: '900', color: 'rgba(255,255,255,0.3)', letterSpacing: '2px' }}>VS</span>
          </div>
          {/* Us */}
          <div style={{ flex: 1, background: 'linear-gradient(135deg,rgba(5,150,105,0.22) 0%,rgba(4,120,87,0.18) 100%)', padding: isMobile ? '14px 16px' : '18px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', fontWeight: '700', letterSpacing: '1.5px', textTransform: 'uppercase', color: '#34d399', marginBottom: '4px' }}>BetBudAI · Live Verified</div>
            <div style={{ fontSize: isMobile ? '28px' : '42px', fontWeight: '900', color: '#34d399', lineHeight: 1, textShadow: '0 0 20px rgba(52,211,153,0.4)' }}>
              {roiLoading ? '…' : roi !== null ? `+${roi}%` : '—'}
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(52,211,153,0.75)', marginTop: '3px' }}>{roiLoading ? '…' : settled ?? '—'} races · no cherry-picking</div>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: isMobile ? '16px' : '28px', flexWrap: 'wrap', marginBottom: isMobile ? '20px' : '28px' }}>
          {[
            { icon: '🤖', label: '20+ signals per horse' },
            { icon: '🎯', label: 'Top 4 official picks + up to 2 watchlist' },
            { icon: '📊', label: 'Every pick logged pre-race' },
            { icon: '📅', label: 'Live since 22 Mar 2026' },
          ].map((p, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '15px' }}>{p.icon}</span>
              <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>{p.label}</span>
            </div>
          ))}
        </div>
      </div>

      {!isAuthenticated && accountSettingsRequest && (
        <div style={{ maxWidth: '620px', margin: '0 auto 20px', padding: '14px 18px', background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.32)', borderRadius: '12px' }}>
          <div style={{ color: '#93c5fd', fontSize: '14px', fontWeight: '800', marginBottom: '6px' }}>Manage your profile settings</div>
          <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '13px', lineHeight: '1.6' }}>
            Sign in to your profile page to unsubscribe from daily picks emails or close your account.
          </div>
          <div style={{ marginTop: '10px' }}>
            <button onClick={() => { setAuthMode('login'); setLoginError(''); }} style={{ background: 'linear-gradient(135deg, #2563eb, #1d4ed8)', border: 'none', borderRadius: '8px', padding: '10px 16px', color: 'white', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>
              Open Profile Sign-In
            </button>
          </div>
        </div>
      )}

      {/* ── COMPACT PRICING STRIP ─────────────────────────────────────── */}
      {!isAuthenticated && (
      <div style={{ marginBottom: '24px' }}>
        <div style={{ textAlign: 'center', marginBottom: '10px', fontSize: '12px', color: 'rgba(255,255,255,0.55)' }}>
          Typical daily card: <strong style={{ color: 'white' }}>{preSignPickCount}</strong> total picks (4 official + up to 2 watchlist). The 1:20pm email includes winners out of total picks. Research/education only, not a betting site, always bet responsibly.
        </div>
        <div style={{ textAlign: 'center', marginBottom: '12px' }}>
          <span style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>⚡ Unlock Your Edge</span>
          <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)', marginLeft: '8px' }}>Start your 7-day free trial</span>
        </div>
        <div style={{ display: 'flex', gap: '10px', maxWidth: '700px', margin: '0 auto', flexWrap: 'wrap', justifyContent: 'center', padding: '0 8px' }}>
          {/* Free Trial */}
          <div style={{ flex: '1 1 180px', maxWidth: isMobile ? '100%' : '220px', background: 'linear-gradient(135deg, rgba(52,211,153,0.12), rgba(16,185,129,0.06))', border: '2px solid rgba(52,211,153,0.4)', borderRadius: '10px', padding: '14px 16px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '-9px', right: '10px', background: 'linear-gradient(135deg, #059669, #047857)', borderRadius: '10px', padding: '2px 8px', fontSize: '8px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '0.5px' }}>7 Days Free</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#34d399' }}>Free Trial</span>
              <span style={{ fontSize: '20px', fontWeight: '900', color: 'white' }}>€0<span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)' }}> for 7 days</span></span>
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', lineHeight: '1.8', marginBottom: '10px' }}>
              ✓ Full Premium access<br/>
              ✓ 4+ tips daily + 2 watchlist picks<br/>
              ✓ Daily featured meeting, results &amp; live ROI<br/>
              ✓ Cancel anytime<br/>
              <span style={{ color: 'rgba(255,255,255,0.4)' }}>No card details required</span><br/>
              <span style={{ color: 'rgba(255,255,255,0.35)' }}>Then €9.99/mo after trial</span>
            </div>
            <button onClick={() => { trackEvent('signup_click', { location: 'home_pricing_strip_free_trial', tier: 'premium_trial', user_status: 'guest' }); setSelectedTrialTier('premium'); setAuthMode('register'); setFormError(''); }} style={{ width: '100%', background: 'linear-gradient(135deg, #059669, #047857)', border: 'none', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>Start Free Trial</button>
          </div>
          {/* Premium */}
          <div style={{ flex: '1 1 180px', maxWidth: isMobile ? '100%' : '220px', background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1))', border: '2px solid rgba(99,102,241,0.5)', borderRadius: '10px', padding: '14px 16px', position: 'relative', boxShadow: '0 0 20px rgba(99,102,241,0.15)' }}>
            <div style={{ position: 'absolute', top: '-9px', right: '10px', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', borderRadius: '10px', padding: '2px 8px', fontSize: '8px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '0.5px' }}>⭐ Popular</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#818cf8' }}>Premium</span>
              <span style={{ fontSize: '20px', fontWeight: '900', color: 'white' }}>€9.99<span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)' }}>/mo</span></span>
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', lineHeight: '1.8', marginBottom: '10px' }}>
              ✓ 4+ Tips Daily<br/>
              ✓ 2 Watchlist Selections Daily<br/>
              ✓ Daily Featured Meeting<br/>
              ✓ All Results<br/>
              ✓ Live ROI Tracking<br/>
              ✓ Priority Support<br/>
              ✓ Cancel Anytime
            </div>
            <button onClick={() => { trackEvent('signup_click', { location: 'home_pricing_strip_premium', tier: 'premium_trial', user_status: 'guest' }); setSelectedTrialTier('premium'); setAuthMode('register'); setFormError(''); }} style={{ width: '100%', background: 'linear-gradient(135deg, #6366f1, #7c3aed)', border: 'none', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>Start Free Trial</button>
          </div>
          {/* VIP Rollers */}
          <div style={{ flex: '1 1 180px', maxWidth: isMobile ? '100%' : '220px', background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(251,191,36,0.06))', border: '2px solid rgba(245,158,11,0.45)', borderRadius: '10px', padding: '14px 16px', position: 'relative', boxShadow: '0 0 20px rgba(245,158,11,0.1)' }}>
            <div style={{ position: 'absolute', top: '-9px', right: '10px', background: 'linear-gradient(135deg, #f59e0b, #d97706)', borderRadius: '10px', padding: '2px 8px', fontSize: '8px', fontWeight: '800', color: 'white', textTransform: 'uppercase', letterSpacing: '0.5px' }}>🔥 Best Value</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', color: '#fbbf24' }}>👑 VIP Rollers</span>
              <span style={{ fontSize: '20px', fontWeight: '900', color: 'white' }}>€49.99<span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)' }}>/mo</span></span>
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', lineHeight: '1.8', marginBottom: '10px' }}>
              ✓ 4+ Tips Daily<br/>
              ✓ 2 Watchlist Selections Daily<br/>
              ✓ Daily Featured Meeting<br/>
              ✓ All Results<br/>
              ✓ Early Ante-Post Major Race Selections<br/>
              ✓ Lay the Vulnerable Favourite<br/>
              ✓ Live ROI Tracking<br/>
              ✓ Major Race Previews<br/>
              ✓ Priority support<br/>
              <span style={{ color: 'rgba(255,255,255,0.4)' }}>⚡ Exchange account required for max benefit</span>
            </div>
            <button onClick={() => { trackEvent('signup_click', { location: 'home_pricing_strip_vip', tier: 'vip_trial', user_status: 'guest' }); setSelectedTrialTier('vip'); setAuthMode('register'); setFormError(''); }} style={{ width: '100%', background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>Start Free Trial</button>
          </div>
        </div>
        <div style={{ textAlign: 'center', fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginTop: '8px' }}>🔒 Powered by Stripe · Cancel anytime · EUR</div>
      </div>
      )}

      {!isAuthenticated && (
        <div style={{ maxWidth: '560px', margin: '0 auto 20px', background: 'linear-gradient(135deg, rgba(225,48,108,0.16), rgba(131,58,180,0.14), rgba(252,176,69,0.12))', border: '1px solid rgba(255,255,255,0.18)', borderRadius: '12px', padding: '12px 14px', textAlign: 'center' }}>
          <div style={{ color: 'white', fontSize: '14px', fontWeight: '800', marginBottom: '6px' }}>Follow BetBudAI on Instagram</div>
          <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', lineHeight: '1.5', marginBottom: '10px' }}>
            Daily updates, race insights and behind-the-scenes AI picks content.
          </div>
          <a
            href="https://www.instagram.com/betbudai?utm_source=qr&igsh=MWg0cWp2a3E3bm5qYw=="
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: 'inline-block', background: 'linear-gradient(135deg,#e1306c 0%,#833ab4 55%,#fcb045 100%)', border: 'none', borderRadius: '8px', color: 'white', padding: '9px 14px', fontSize: '12px', fontWeight: '800', textDecoration: 'none', letterSpacing: '0.3px' }}
          >
            📸 Follow @betbudai
          </a>
        </div>
      )}

      {/* ── AUTH SECTION ──────────────────────────────────────────────── */}
      {isAuthenticated ? (
        <div style={{ marginBottom: '40px' }}>
          <div style={{ textAlign: 'center', padding: '24px 24px 16px', background: 'rgba(5,150,105,0.08)', border: '1px solid rgba(52,211,153,0.25)', borderRadius: '16px', marginBottom: '24px' }}>
            <h3 style={{ color: '#34d399', fontSize: '20px', fontWeight: '800', margin: '0 0 6px' }}>✅ You're signed in!</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', margin: 0 }}>Use the tabs above to access today's picks, results and more.</p>
          </div>
          <UpgradeCards authUser={authUser} />
        </div>
      ) : (
      <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '16px', padding: isMobile ? '24px 16px' : '36px 32px', marginBottom: '40px' }}>

        {/* Mode toggle */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '28px' }}>
          {[{ mode: 'register', label: 'Create Account' }, { mode: 'login', label: 'Sign In' }].map(t => (
            <button key={t.mode} onClick={() => { setAuthMode(t.mode); setFormError(''); setLoginError(''); }} style={{
              padding: '9px 28px', borderRadius: '20px',
              border: authMode === t.mode ? '2px solid #34d399' : '2px solid rgba(255,255,255,0.15)',
              background: authMode === t.mode ? 'rgba(52,211,153,0.15)' : 'transparent',
              color: authMode === t.mode ? '#34d399' : 'rgba(255,255,255,0.45)',
              fontWeight: '700', fontSize: '14px', cursor: 'pointer', transition: 'all 0.2s',
            }}>{t.label}</button>
          ))}
        </div>

        {authMode === 'forgot' ? (
          /* ── FORGOT PASSWORD FORM ───────────────────────────────────── */
          forgotState === 'sent' ? (
            <div style={{ textAlign: 'center', maxWidth: '420px', margin: '0 auto' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>📧</div>
              <h3 style={{ color: '#34d399', fontSize: '20px', fontWeight: '800', margin: '0 0 12px' }}>Check Your Email</h3>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', lineHeight: '1.6', margin: '0 0 20px' }}>If an account exists for <strong style={{ color: 'white' }}>{forgotEmail}</strong>, we've sent a password reset link. Check your inbox (and spam folder).</p>
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px', margin: '0 0 16px' }}>The link expires in 1 hour.</p>
              <button type="button" onClick={() => { setAuthMode('login'); setForgotState('idle'); setForgotEmail(''); }} style={{ background: 'none', border: 'none', color: '#34d399', fontSize: '13px', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>← Back to Sign In</button>
            </div>
          ) : (
            <form onSubmit={handleForgotSubmit} noValidate>
              <h3 style={{ color: 'white', fontSize: '20px', fontWeight: '800', margin: '0 0 8px', textAlign: 'center' }}>Reset Your Password</h3>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', textAlign: 'center', margin: '0 0 24px' }}>Enter your email address and we'll send you a link to reset your password.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '420px', margin: '0 auto 20px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <label style={labelStyle}>Email Address</label>
                  <input style={inputStyle} type="email" value={forgotEmail} onChange={e => setForgotEmail(e.target.value)} placeholder="jane@example.com" autoComplete="email" required />
                </div>
              </div>
              {forgotError && (
                <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', color: '#f87171', fontSize: '14px', maxWidth: '420px', margin: '0 auto 18px' }}>
                  ⚠ {forgotError}
                </div>
              )}
              <div style={{ maxWidth: '420px', margin: '0 auto' }}>
                <button type="submit" disabled={forgotState === 'loading'} style={{
                  width: '100%', padding: '14px', borderRadius: '10px', border: 'none',
                  cursor: forgotState === 'loading' ? 'not-allowed' : 'pointer',
                  background: forgotState === 'loading' ? 'rgba(5,150,105,0.5)' : 'linear-gradient(135deg,#059669 0%,#047857 100%)',
                  color: 'white', fontSize: '16px', fontWeight: '800', transition: 'all 0.2s',
                }}>
                  {forgotState === 'loading' ? '⏳ Sending…' : '📧 Send Reset Link'}
                </button>
              </div>
              <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', textAlign: 'center', marginTop: '16px', marginBottom: 0 }}>
                Remember your password?{' '}
                <button type="button" onClick={() => { setAuthMode('login'); setForgotError(''); }} style={{ background: 'none', border: 'none', color: '#34d399', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>Sign in here</button>
              </p>
              <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', textAlign: 'center', marginTop: '8px', marginBottom: 0 }}>
                Need help? Contact us at{' '}
                <a href="mailto:directorai@futuregenai.com" style={{ color: '#34d399', textDecoration: 'underline' }}>directorai@futuregenai.com</a>
              </p>
            </form>
          )
        ) : authMode === 'reset' ? (
          /* ── RESET PASSWORD FORM ────────────────────────────────────── */
          resetState === 'success' ? (
            <div style={{ textAlign: 'center', maxWidth: '420px', margin: '0 auto' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>✅</div>
              <h3 style={{ color: '#34d399', fontSize: '20px', fontWeight: '800', margin: '0 0 12px' }}>Password Reset!</h3>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', margin: '0 0 20px' }}>Your password has been updated. You can now sign in with your new password.</p>
              <button type="button" onClick={() => { setAuthMode('login'); setResetState('idle'); setResetForm({ password: '', confirmPassword: '' }); }} style={{
                padding: '14px 32px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                background: 'linear-gradient(135deg,#059669 0%,#047857 100%)',
                color: 'white', fontSize: '16px', fontWeight: '800',
              }}>🔑 Sign In Now</button>
            </div>
          ) : (
            <form onSubmit={handleResetSubmit} noValidate>
              <h3 style={{ color: 'white', fontSize: '20px', fontWeight: '800', margin: '0 0 8px', textAlign: 'center' }}>Set New Password</h3>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', textAlign: 'center', margin: '0 0 24px' }}>Enter your new password below.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '420px', margin: '0 auto 20px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <label style={labelStyle}>New Password</label>
                  <input style={inputStyle} type="password" value={resetForm.password} onChange={e => setResetForm(p => ({ ...p, password: e.target.value }))} placeholder="Min. 8 characters" autoComplete="new-password" required />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <label style={labelStyle}>Confirm New Password</label>
                  <input style={inputStyle} type="password" value={resetForm.confirmPassword} onChange={e => setResetForm(p => ({ ...p, confirmPassword: e.target.value }))} placeholder="Repeat password" autoComplete="new-password" required />
                </div>
              </div>
              {resetError && (
                <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', color: '#f87171', fontSize: '14px', maxWidth: '420px', margin: '0 auto 18px' }}>
                  ⚠ {resetError}
                </div>
              )}
              <div style={{ maxWidth: '420px', margin: '0 auto' }}>
                <button type="submit" disabled={resetState === 'loading'} style={{
                  width: '100%', padding: '14px', borderRadius: '10px', border: 'none',
                  cursor: resetState === 'loading' ? 'not-allowed' : 'pointer',
                  background: resetState === 'loading' ? 'rgba(5,150,105,0.5)' : 'linear-gradient(135deg,#059669 0%,#047857 100%)',
                  color: 'white', fontSize: '16px', fontWeight: '800', transition: 'all 0.2s',
                }}>
                  {resetState === 'loading' ? '⏳ Resetting…' : '🔒 Set New Password'}
                </button>
              </div>
            </form>
          )
        ) : authMode === 'login' ? (
          /* ── LOGIN FORM ─────────────────────────────────────────────── */
          <form onSubmit={handleLoginSubmit} noValidate autoComplete="on">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '420px', margin: '0 auto 20px' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={labelStyle}>Email or Username</label>
                <input style={inputStyle} type="text" name="emailOrUser" value={loginForm.emailOrUser} onChange={handleLoginChange} placeholder="jane@example.com or punter_99" autoComplete="username" required />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={labelStyle}>Password</label>
                <input style={inputStyle} type="password" name="password" value={loginForm.password} onChange={handleLoginChange} placeholder="Your password" autoComplete="current-password" required />
              </div>
            </div>
            {loginError && (
              <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', color: '#f87171', fontSize: '14px', marginBottom: '18px', maxWidth: '420px', margin: '0 auto 18px' }}>
                ⚠ {loginError}
              </div>
            )}
            <div style={{ maxWidth: '420px', margin: '0 auto' }}>
              <button type="submit" disabled={loginState === 'loading'} style={{
                width: '100%', padding: '14px', borderRadius: '10px', border: 'none',
                cursor: loginState === 'loading' ? 'not-allowed' : 'pointer',
                background: loginState === 'loading' ? 'rgba(5,150,105,0.5)' : 'linear-gradient(135deg,#059669 0%,#047857 100%)',
                color: 'white', fontSize: '16px', fontWeight: '800', transition: 'all 0.2s',
              }}>
                {loginState === 'loading' ? '⏳ Signing in…' : '🔑 Sign In'}
              </button>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '12px', textAlign: 'center', marginTop: '12px', marginBottom: '4px' }}>
              <button type="button" onClick={() => { setAuthMode('forgot'); setForgotError(''); setForgotState('idle'); }} style={{ background: 'none', border: 'none', color: '#34d399', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>Forgot your password?</button>
            </p>
            <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', textAlign: 'center', marginTop: '4px', marginBottom: 0 }}>
              Don't have an account?{' '}
              <button type="button" onClick={() => setAuthMode('register')} style={{ background: 'none', border: 'none', color: '#34d399', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>Start a free trial</button>
            </p>
          </form>
        ) : (
          /* ── REGISTER FORM ──────────────────────────────────────────── */
          <>
        <h3 style={{ color: 'white', fontSize: '22px', fontWeight: '800', margin: '0 0 6px', textAlign: 'center' }}>Start Your 7-Day {selectedTrialLabel} Trial</h3>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px', textAlign: 'center', margin: '0 0 8px' }}>Immediate {selectedTrialLabel} access for 7 days — no card details required.</p>
        <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '12px', textAlign: 'center', margin: '0 0 28px' }}>Cancel anytime. If you want to continue after the trial, the plan is {selectedTrialPrice}/mo.</p>

        <form onSubmit={handleSubmit} noValidate autoComplete="off">
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit,minmax(240px,1fr))', gap: '14px', marginBottom: '18px' }}>

            <div style={fieldStyle}>
              <label style={labelStyle}>Full Name</label>
              <input style={inputStyle} type="text" name="fullName" value={form.fullName} onChange={handleChange} placeholder="Jane Smith" maxLength={100} required />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>Email Address</label>
              <input style={inputStyle} type="email" name="email" value={form.email} onChange={handleChange} placeholder="jane@example.com" maxLength={254} required />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>Age</label>
              <input style={inputStyle} type="number" name="age" value={form.age} onChange={handleChange} placeholder="Must be 18+" min={18} max={120} required />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>Username</label>
              <input style={inputStyle} type="text" name="username" value={form.username} onChange={handleChange} placeholder="e.g. Henrik0707 or punter_99" maxLength={30} required />
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '4px' }}>Letters, numbers and underscores only — no spaces or special characters</div>
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>Password</label>
              <input style={inputStyle} type="password" name="password" value={form.password} onChange={handleChange} placeholder="Min. 8 characters" maxLength={128} required />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>Confirm Password</label>
              <input style={inputStyle} type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange} placeholder="Repeat password" maxLength={128} required />
            </div>

          </div>

          {/* T&C */}
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', marginBottom: '20px' }}>
            <input type="checkbox" name="agreeTerms" checked={form.agreeTerms} onChange={handleChange}
              style={{ width: '18px', height: '18px', flexShrink: 0, marginTop: '1px', accentColor: '#10b981', cursor: 'pointer' }} />
            <span style={{ color: 'rgba(255,255,255,0.65)', fontSize: '13px', lineHeight: '1.5' }}>
              I confirm I am 18 or over and agree to the{' '}
              <a href="/terms.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'underline' }}>Terms &amp; Conditions</a>
              {' '}and{' '}
              <a href="/privacy.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'underline' }}>Privacy Policy</a>.
              BetBudAI is for research and educational purposes only and is not betting advice. Daily picks-ready emails are informational and selections may still change due to late race-day updates. Please gamble responsibly.
            </span>
          </label>

          {formError && (
            <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', color: '#f87171', fontSize: '14px', marginBottom: '18px' }}>
              ⚠ {formError}
            </div>
          )}

          <button type="submit" disabled={formState === 'loading'} style={{
            width: '100%', padding: '14px', borderRadius: '10px', border: 'none', cursor: formState === 'loading' ? 'not-allowed' : 'pointer',
            background: formState === 'loading' ? 'rgba(5,150,105,0.5)' : 'linear-gradient(135deg,#059669 0%,#047857 100%)',
            color: 'white', fontSize: '16px', fontWeight: '800', letterSpacing: '0.5px', transition: 'all 0.2s',
          }}>
            {formState === 'loading' ? '⏳ Creating account…' : '🚀 Start My Free Trial'}
          </button>
        </form>

        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', textAlign: 'center', marginTop: '16px', marginBottom: 0 }}>
          🔒 Your data is stored securely. We never share your details with third parties.{' '}
          Already have an account?{' '}
          <button type="button" onClick={() => setAuthMode('login')} style={{ background: 'none', border: 'none', color: '#34d399', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>Sign in here</button>
        </p>
          </>
        )}
      </div>
      )}

      {/* Responsible gambling footer */}
      <div style={{ textAlign: 'center', padding: '0 0 24px', color: 'rgba(255,255,255,0.25)', fontSize: '12px', lineHeight: '1.6' }}>
        BetBudAI provides data analysis for informational purposes only and does not constitute financial or betting advice.<br />
        Please gamble responsibly. Visit <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer" style={{ color: 'rgba(255,255,255,0.4)' }}>BeGambleAware.org</a> for support.<br />
        Questions? Contact us at <a href="mailto:directorai@futuregenai.com" style={{ color: 'rgba(255,255,255,0.4)' }}>directorai@futuregenai.com</a>
      </div>

      <LegalDisclaimerCard style={{ maxWidth: '700px', margin: '28px auto 0' }} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ADMIN VIEW
// ─────────────────────────────────────────────────────────────────────────────

const WEIGHT_GROUPS = [
  {
    label: 'Form & Recent Performance',
    keys: [
      { key: 'recent_win',           label: 'Recent Win Bonus',          desc: 'Won last race' },
      { key: 'total_wins',           label: 'Total Wins Weight',         desc: 'Career wins count' },
      { key: 'consistency',          label: 'Consistency Bonus',         desc: 'Place record / consistency' },
      { key: 'bounce_back_bonus',    label: 'Bounce-back Bonus',         desc: 'After a below-par run' },
      { key: 'short_form_improvement', label: 'Short Form Improvement',  desc: 'Improving form trend' },
      { key: 'database_history',     label: 'Database History',          desc: 'Previous DB results here' },
    ],
  },
  {
    label: 'Deep Form Signals',
    keys: [
      { key: 'form_exact_course_win',   label: 'Course Winner (exact)',     desc: 'Won at this exact course' },
      { key: 'form_exact_distance_win', label: 'Distance Winner (exact)',   desc: 'Won at today\'s distance (±0.5f)' },
      { key: 'form_going_win',          label: 'Going Win',                 desc: 'Won on same going type' },
      { key: 'form_going_place',        label: 'Going Place',               desc: 'Placed on same going' },
      { key: 'form_fresh_optimal',      label: 'Fresh & Optimal',           desc: 'Last run 14-35 days ago' },
      { key: 'form_close_2nd',          label: 'Close 2nd Last Time',       desc: '2nd beaten <4 lengths' },
      { key: 'form_or_rising',          label: 'Official Rating Rising',    desc: 'OR improving over last 3 runs' },
      { key: 'form_big_field_win',      label: 'Big Field Win',             desc: 'Won in field of 10+ runners' },
    ],
  },
  {
    label: 'Course, Distance & Going',
    keys: [
      { key: 'cd_bonus',              label: 'C&D Winner Bonus',            desc: 'Won at this course + distance' },
      { key: 'graded_race_cd_bonus',  label: 'Graded Race C&D Bonus',       desc: 'C&D form in a graded race' },
      { key: 'course_bonus',          label: 'Course Bonus',                desc: 'Previous wins at this course' },
      { key: 'distance_suitability',  label: 'Distance Suitability',        desc: 'Proven at today\'s distance' },
      { key: 'going_suitability',     label: 'Going Suitability',           desc: 'Suited to today\'s going' },
      { key: 'track_pattern_bonus',   label: 'Track Pattern Bonus',         desc: 'Left/right-hand track preference' },
    ],
  },
  {
    label: 'Market & Odds',
    keys: [
      { key: 'sweet_spot',          label: 'Sweet-spot Odds',           desc: 'Odds in the model\'s preferred range' },
      { key: 'optimal_odds',        label: 'Optimal Odds Position',     desc: 'Clean odds signal near sweet spot' },
      { key: 'favorite_correction', label: 'Favourite Correction',      desc: 'Cap stacking when trainer bonus overlaps fav signal' },
    ],
  },
  {
    label: 'Trainer & Jockey',
    keys: [
      { key: 'trainer_reputation',      label: 'Trainer Tier 1 (Elite)',    desc: 'Top-tier trainers (Mullins, O\'Brien…)' },
      { key: 'trainer_tier2',           label: 'Trainer Tier 2',            desc: 'Good trainers with strong records' },
      { key: 'trainer_tier3',           label: 'Trainer Tier 3',            desc: 'Decent trainers with consistent form' },
      { key: 'jockey_quality',          label: 'Jockey Tier 1 (Elite)',     desc: 'Top-tier jockeys' },
      { key: 'jockey_tier2',            label: 'Jockey Tier 2',             desc: 'Champion-level jockeys' },
      { key: 'jockey_course_bonus',     label: 'Jockey Course Bonus',       desc: 'Jockey excels at this course' },
    ],
  },
  {
    label: 'Meeting Focus & Targeting',
    keys: [
      { key: 'meeting_focus_trainer',   label: 'Trainer Sole Meeting Runner', desc: 'Trainer\'s only runner at this meeting' },
      { key: 'meeting_focus_jockey',    label: 'Jockey Sole Meeting Rider',   desc: 'Jockey\'s only ride at this meeting' },
      { key: 'meeting_focus_combo',     label: 'Trainer+Jockey Focus Combo',  desc: 'Both focused on this race' },
      { key: 'new_trainer_debut',       label: 'New Trainer Debut',           desc: 'No prior DB record with this trainer' },
    ],
  },
  {
    label: 'Class, Age & Special Signals',
    keys: [
      { key: 'official_rating_bonus',   label: 'Official Rating Bonus',       desc: 'High OR = class horse' },
      { key: 'age_bonus',               label: 'Age Bonus',                   desc: '4-6yo flat: prime racing age' },
      { key: 'relative_weight_bonus',   label: 'Relative Weight Bonus',       desc: 'Carrying less than field average' },
      { key: 'weight_penalty',          label: 'Carried Weight Penalty',      desc: 'Penalised for weight carried' },
      { key: 'class_drop_bonus',        label: 'Class Drop Bonus',            desc: 'Dropped from Class 2/3 → Class 4/5+' },
      { key: 'unexposed_bonus',         label: 'Unexposed Horse Bonus',       desc: '≤5yo, ≤5 runs, 0 wins, 1+ place, 4-10 odds' },
    ],
  },
  {
    label: 'Penalties',
    penalty: true,
    keys: [
      { key: 'novice_race_penalty',        label: 'Novice Race Penalty',         desc: 'Maiden/novice race — unknown quantities' },
      { key: 'aw_low_class_penalty',       label: 'AW Low-class Penalty',        desc: 'All-weather Class 5/6 races' },
      { key: 'heavy_going_penalty',        label: 'Heavy Going Penalty',         desc: 'Heavy ground = high variance' },
      { key: 'aw_evening_penalty',         label: 'AW Evening Penalty',          desc: 'All-weather after 17:30 UTC' },
      { key: 'unknown_trainer_penalty',    label: 'Unknown Trainer Penalty',     desc: 'Trainer not in any tier list' },
      { key: 'large_field_penalty',        label: 'Large Field Penalty',         desc: '16-19 runners: this value; 20+: ×1.8' },
      { key: 'same_trainer_rival_penalty', label: 'Same-trainer Rival Penalty',  desc: 'Trainer has 2+ in same race' },
      { key: 'irish_handicap_penalty',     label: 'Irish Handicap Penalty',      desc: 'Handicap at Curragh/Dundalk/Navan/Naas/Leopardstown' },
    ],
  },
];

const CONFIG_FIELDS = [
  { key: 'elite_threshold',       label: 'ELITE Score Threshold',       desc: 'Score ≥ this = ELITE confidence', min: 80, max: 100, step: 1  },
  { key: 'strong_threshold',      label: 'STRONG Score Threshold',      desc: 'Score ≥ this = STRONG confidence', min: 70, max: 99,  step: 1  },
  { key: 'good_threshold',        label: 'GOOD Score Threshold',        desc: 'Score ≥ this = GOOD confidence',   min: 60, max: 95,  step: 1  },
  { key: 'fair_threshold',        label: 'FAIR Score Threshold',        desc: 'Score ≥ this = FAIR confidence',   min: 40, max: 85,  step: 1  },
  { key: 'risky_threshold',       label: 'RISKY Score Threshold',       desc: 'Score ≥ this = RISKY (below = POOR)', min: 20, max: 70, step: 1 },
  { key: 'min_confidence',        label: 'Min Confidence (global)',     desc: 'Global floor — fallback floor score', min: 50, max: 95, step: 1 },
  { key: 'min_confidence_hcap',   label: 'Min Confidence (Handicaps)', desc: 'Handicap races need higher conviction', min: 60, max: 99, step: 1 },
  { key: 'min_confidence_norace', label: 'Min Confidence (Conditions)',desc: 'Conditions/maiden/novice races', min: 50, max: 95, step: 1 },
  { key: 'target_picks',          label: 'Target Picks per Day',       desc: 'Max morning picks shown in UI', min: 1, max: 10, step: 1 },
  { key: 'picks_gate_hour_utc',   label: 'Picks Gate Hour (UTC)',      desc: '1pm BST = 12 UTC. Picks hidden until this hour', min: 0, max: 23, step: 1 },
];

function AdminView({ authUser }) {
  const [weights, setWeights]           = useState(null);
  const [config, setConfig]             = useState(null);
  const [defaultWeights, setDefaultWeights] = useState({});
  const [defaultConfig, setDefaultConfig]   = useState({});
  const [savedAt, setSavedAt]           = useState(null);
  const [loading, setLoading]           = useState(true);
  const [saving, setSaving]             = useState(false);
  const [saveMsg, setSaveMsg]           = useState(null);
  const [activeSection, setActiveSection] = useState('analytics');
  const [subscribers, setSubscribers]   = useState(null);
  const [subscriberTierDrafts, setSubscriberTierDrafts] = useState({});
  const [subscriberRoleSaving, setSubscriberRoleSaving] = useState({});
  const [losspicks, setLosspicks]         = useState(null);
  const [lossLoading, setLossLoading]    = useState(false);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsMsg, setAnalyticsMsg] = useState(null);

  const [majorRunning, setMajorRunning] = useState(false);
  const [majorMsg, setMajorMsg]         = useState(null);
  const gaMeasurementId = process.env.REACT_APP_GA_MEASUREMENT_ID || 'not set';
  const trackedEvents = [
    'page_view',
    'view_pricing',
    'signup_click',
    'begin_checkout',
    'subscription_started',
  ];

  const adminToken = authUser?.admin_token;

  useEffect(() => {
    if (!adminToken) return;
    setLoading(true);
    fetch(`${API_BASE_URL}/api/admin/config`, {
      headers: { 'x-admin-token': adminToken }
    })
      .then(r => {
        if (r.status === 403) {
          setSaveMsg({ ok: false, text: '⚠️ Admin session expired. Please log out and log back in.' });
          return null;
        }
        return r.json();
      })
      .then(data => {
        if (!data) return;
        if (data.success) {
          setWeights(data.weights || data.default_weights);
          setConfig(data.config || data.default_config);
          setDefaultWeights(data.default_weights || {});
          setDefaultConfig(data.default_config || {});
          setSavedAt(data.weights_saved_at || data.config_saved_at);
        }
      })
      .catch(e => console.error('Admin config load error', e))
      .finally(() => setLoading(false));
  }, [adminToken]);

  useEffect(() => {
    if (!adminToken || activeSection !== 'analytics') return;
    const controller = new AbortController();
    setAnalyticsLoading(true);
    setAnalyticsMsg(null);
    fetch(`${API_BASE_URL}/api/admin/analytics`, {
      headers: { 'x-admin-token': adminToken },
      signal: controller.signal,
    })
      .then(r => r.json())
      .then(data => {
        if (data?.success) {
          setAnalyticsSummary(data);
          setAnalyticsMsg(data.configured ? null : { ok: false, text: data.message || 'GA4 reporting is not configured yet.' });
        } else {
          setAnalyticsSummary(data || null);
          setAnalyticsMsg({ ok: false, text: data?.error || data?.message || 'Failed to load GA4 summary.' });
        }
      })
      .catch(e => {
        if (e.name !== 'AbortError') {
          setAnalyticsMsg({ ok: false, text: `❌ Network error: ${e.message}` });
        }
      })
      .finally(() => setAnalyticsLoading(false));
    return () => controller.abort();
  }, [adminToken, activeSection]);

  const handleSave = () => {
    if (!adminToken) return;
    setSaving(true);
    setSaveMsg(null);
    fetch(`${API_BASE_URL}/api/admin/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-admin-token': adminToken },
      body: JSON.stringify({ weights, config }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          setSaveMsg({ ok: true, text: `✅ Saved at ${new Date().toLocaleTimeString('en-GB')}` });
          setSavedAt(data.saved_at);
        } else {
          setSaveMsg({ ok: false, text: `❌ Save failed: ${data.error}` });
        }
      })
      .catch(e => setSaveMsg({ ok: false, text: `❌ Network error: ${e.message}` }))
      .finally(() => setSaving(false));
  };

  const handleReset = (which) => {
    if (which === 'weights') setWeights({ ...defaultWeights });
    else setConfig({ ...defaultConfig });
  };

  const loadSubscribers = () => {
    fetch(`${API_BASE_URL}/api/admin/subscribers`, {
      headers: { 'x-admin-token': adminToken }
    })
      .then(r => {
        if (r.status === 403) { setSaveMsg({ ok: false, text: '⚠️ Admin session expired. Please log out and log back in.' }); return null; }
        return r.json();
      })
      .then(data => {
        if (data && data.success) {
          const list = data.users || data.subscribers || [];
          setSubscribers(list);
          const drafts = {};
          list.forEach((u) => {
            drafts[u.email] = (u.subscription_tier || u.role || 'free');
          });
          setSubscriberTierDrafts(drafts);
        }
      })
      .catch(e => console.error('Subscribers load error', e));
  };

  const saveSubscriberTier = (email) => {
    const tier = (subscriberTierDrafts[email] || 'free').toLowerCase();
    setSubscriberRoleSaving(prev => ({ ...prev, [email]: true }));
    fetch(`${API_BASE_URL}/api/admin/subscribers/role`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-admin-token': adminToken },
      body: JSON.stringify({ email, tier }),
    })
      .then(r => r.json())
      .then(data => {
        if (data && data.success) {
          setSubscribers(prev => (prev || []).map(u => u.email === email
            ? { ...u, ...(data.updated_user || {}), role: tier, subscription_tier: tier }
            : u));
          setSaveMsg({ ok: true, text: `✅ ${email} updated to ${tier}` });
        } else {
          setSaveMsg({ ok: false, text: `❌ Update failed: ${data?.error || 'Unknown error'}` });
        }
      })
      .catch(e => setSaveMsg({ ok: false, text: `❌ Network error: ${e.message}` }))
      .finally(() => setSubscriberRoleSaving(prev => ({ ...prev, [email]: false })));
  };

  const loadLossPicks = () => {
    setLossLoading(true);
    Promise.all([
      fetch(API_BASE_URL + '/api/results/today').then(r => r.json()),
      fetch(API_BASE_URL + '/api/results/yesterday').then(r => r.json()),
    ])
      .then(([todayData, yestData]) => {
        const todayPicks = (todayData.success ? todayData.picks || [] : []).map(p => ({ ...p, _dayLabel: 'Today' }));
        const yestPicks  = (yestData.success  ? yestData.picks  || [] : []).map(p => ({ ...p, _dayLabel: 'Yesterday' }));
        const deduped = {};
        [...todayPicks, ...yestPicks].forEach(p => {
          const key = (p.course || '') + '|' + (p.race_time || '').substring(0, 16);
          const sc  = parseFloat(p.comprehensive_score || p.analysis_score || 0);
          if (!deduped[key] || sc > parseFloat(deduped[key].comprehensive_score || deduped[key].analysis_score || 0)) deduped[key] = p;
        });
        setLosspicks(Object.values(deduped));
      })
      .catch(e => console.error('Loss picks load error', e))
      .finally(() => setLossLoading(false));
  };

  if (!adminToken) {
    return (
      <div style={{ textAlign:'center', padding:'60px 20px', color:'#f87171' }}>
        <div style={{ fontSize:'48px' }}>🔒</div>
        <div style={{ fontSize:'18px', marginTop:'16px' }}>Admin session expired. Please sign out and sign back in.</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ textAlign:'center', padding:'60px 20px', color:'#34d399' }}>
        <div style={{ fontSize:'32px' }}>⚙️</div>
        <div style={{ marginTop:'12px', fontSize:'16px' }}>Loading admin configuration…</div>
      </div>
    );
  }

  const sectionBtnStyle = (key) => ({
    background: activeSection === key ? 'rgba(124,58,237,0.35)' : 'rgba(255,255,255,0.07)',
    border: activeSection === key ? '1px solid rgba(167,139,250,0.6)' : '1px solid rgba(255,255,255,0.15)',
    borderRadius: '8px', color: 'white', padding: '8px 18px', cursor: 'pointer',
    fontSize: '13px', fontWeight: activeSection === key ? '700' : '400',
    transition: 'all 0.15s',
  });

  return (
    <div style={{ maxWidth: '920px', margin: '0 auto', padding: '0 0 60px' }}>

      {/* Header */}
      <div style={{ background:'rgba(124,58,237,0.12)', border:'1px solid rgba(167,139,250,0.3)', borderRadius:'14px', padding:'20px 24px', marginBottom:'24px', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'12px' }}>
        <div>
          <div style={{ fontSize:'20px', fontWeight:'800', color:'#c4b5fd' }}>⚙️ System Configuration</div>
          <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>
            Signed in as <strong style={{ color:'#a78bfa' }}>{authUser?.username || authUser?.email}</strong>
            {savedAt && <span> · Last saved: {new Date(savedAt).toLocaleString('en-GB')}</span>}
          </div>
        </div>
        <div style={{ display:'flex', gap:'8px', flexWrap:'wrap' }}>
          {saveMsg && (
            <span style={{ fontSize:'13px', color: saveMsg.ok ? '#34d399' : '#f87171', padding:'6px 12px', background: saveMsg.ok ? 'rgba(5,150,105,0.1)' : 'rgba(239,68,68,0.1)', borderRadius:'6px', border:`1px solid ${saveMsg.ok ? 'rgba(52,211,153,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
              {saveMsg.text}
            </span>
          )}
          <button onClick={handleSave} disabled={saving} style={{ background: saving ? 'rgba(124,58,237,0.3)' : 'linear-gradient(135deg,#7c3aed,#5b21b6)', border:'none', borderRadius:'8px', color:'white', padding:'9px 22px', cursor: saving ? 'not-allowed' : 'pointer', fontWeight:'700', fontSize:'14px' }}>
            {saving ? '⏳ Saving…' : '💾 Save All Changes'}
          </button>
        </div>
      </div>

      {/* Section Nav */}
      <div style={{ display:'flex', gap:'8px', marginBottom:'24px', flexWrap:'wrap' }}>
        <button style={sectionBtnStyle('analytics')} onClick={() => setActiveSection('analytics')}>📈 Site Analytics</button>
        <button style={sectionBtnStyle('weights')} onClick={() => setActiveSection('weights')}>⚖️ Scoring Weights</button>
        <button style={sectionBtnStyle('lossanalysis')} onClick={() => { setActiveSection('lossanalysis'); if (!losspicks) loadLossPicks(); }}>🔍 Loss Analysis</button>
        <button style={sectionBtnStyle('subscribers')} onClick={() => { setActiveSection('subscribers'); if (!subscribers) loadSubscribers(); }}>👥 Subscribers</button>
        <button style={sectionBtnStyle('majoranalysis')} onClick={() => setActiveSection('majoranalysis')}>🏆 Major Races AI</button>
      </div>

      {/* ─── Score Thresholds ─── */}
      {activeSection === 'config' && config && (
        <div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'16px' }}>
            <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0' }}>Score Thresholds &amp; Timing</div>
            <button onClick={() => handleReset('config')} style={{ background:'rgba(255,255,255,0.07)', border:'1px solid rgba(255,255,255,0.17)', borderRadius:'6px', color:'rgba(255,255,255,0.6)', padding:'5px 14px', cursor:'pointer', fontSize:'12px' }}>↩ Reset to defaults</button>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(min(100%,420px),1fr))', gap:'12px' }}>
            {CONFIG_FIELDS.map(f => (
              <AdminSliderRow
                key={f.key}
                label={f.label}
                desc={f.desc}
                value={config[f.key] ?? defaultConfig[f.key] ?? 0}
                defaultValue={defaultConfig[f.key] ?? 0}
                min={f.min}
                max={f.max}
                step={f.step}
                onChange={v => setConfig(c => ({ ...c, [f.key]: v }))}
              />
            ))}
          </div>
        </div>
      )}

      {/* ─── Scoring Weights ─── */}
      {activeSection === 'weights' && weights && (
        <div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'16px' }}>
            <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0' }}>Scoring Weights</div>
            <button onClick={() => handleReset('weights')} style={{ background:'rgba(255,255,255,0.07)', border:'1px solid rgba(255,255,255,0.17)', borderRadius:'6px', color:'rgba(255,255,255,0.6)', padding:'5px 14px', cursor:'pointer', fontSize:'12px' }}>↩ Reset to defaults</button>
          </div>
          {WEIGHT_GROUPS.map(group => (
            <div key={group.label} style={{ marginBottom:'28px' }}>
              <div style={{ fontSize:'13px', fontWeight:'700', color: group.penalty ? '#fca5a5' : '#a78bfa', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:'10px', borderBottom: `1px solid ${group.penalty ? 'rgba(252,165,165,0.2)' : 'rgba(167,139,250,0.2)'}`, paddingBottom:'6px' }}>
                {group.penalty ? '⚠ ' : ''}{group.label}
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(min(100%,420px),1fr))', gap:'10px' }}>
                {group.keys.map(({ key, label, desc }) => (
                  <AdminSliderRow
                    key={key}
                    label={label}
                    desc={desc}
                    value={weights[key] ?? defaultWeights[key] ?? 0}
                    defaultValue={defaultWeights[key] ?? 0}
                    min={0}
                    max={group.penalty ? 60 : 30}
                    step={1}
                    penalty={group.penalty}
                    onChange={v => setWeights(w => ({ ...w, [key]: v }))}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ─── Loss Analysis ─── */}
      {activeSection === 'lossanalysis' && (
        <div>
          <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0', marginBottom:'4px' }}>🔍 Loss Analysis — Why We Missed</div>
          <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.45)', marginBottom:'20px' }}>For each loss/placed pick: how the real winner ranked in our model and which scoring factors were over-weighted.</div>
          {lossLoading ? (
            <div style={{ textAlign:'center', padding:'40px', color:'rgba(255,255,255,0.4)' }}>Loading results…</div>
          ) : (
            <LossAnalysisPanel picks={losspicks || []} />
          )}
        </div>
      )}

      {/* ─── Subscribers ─── */}
      {activeSection === 'subscribers' && (
        <div>
          <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0', marginBottom:'16px' }}>👥 Subscribers</div>
          {!subscribers ? (
            <div style={{ color:'rgba(255,255,255,0.5)', padding:'20px', textAlign:'center' }}>Loading…</div>
          ) : (() => {
            const total      = subscribers.length;
            const verified   = subscribers.filter(u => u.email_verified).length;
            const admins     = subscribers.filter(u => u.role === 'admin').length;
            const now        = new Date();
            const sevenAgo   = new Date(now - 7 * 86400000).toISOString();
            const thirtyAgo  = new Date(now - 30 * 86400000).toISOString();
            const active7    = subscribers.filter(u => (u.last_login || '') >= sevenAgo).length;
            const active30   = subscribers.filter(u => (u.last_login || '') >= thirtyAgo).length;
            const fmtDate = (s, isLogin) => {
              if (!s) return '—';
              try {
                const d = new Date(s);
                const diffMin = Math.floor((now - d) / 60000);
                if (isLogin && diffMin < 15) return '🟢 Active';
                const diff = Math.floor((now - d) / 86400000);
                if (diff === 0) return 'Today';
                if (diff === 1) return 'Yesterday';
                if (diff < 7)  return `${diff}d ago`;
                return d.toLocaleDateString('en-GB', { day:'numeric', month:'short' });
              } catch { return s.slice(0,10); }
            };
            return (
              <>
                {/* Summary stats */}
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(110px,1fr))', gap:'10px', marginBottom:'20px' }}>
                  {[
                    { label:'Total', value: total, color:'#93c5fd' },
                    { label:'Verified', value: verified, color:'#34d399' },
                    { label:'Active 7d', value: active7, color:'#fbbf24' },
                    { label:'Active 30d', value: active30, color:'#a78bfa' },
                    { label:'Admins', value: admins, color:'#f87171' },
                  ].map(s => (
                    <div key={s.label} style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px', padding:'12px', textAlign:'center' }}>
                      <div style={{ fontSize:'22px', fontWeight:'900', color: s.color }}>{s.value}</div>
                      <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'2px' }}>{s.label}</div>
                    </div>
                  ))}

                </div>

                {/* Table */}
                <div style={{ overflowX:'auto' }}>
                  <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
                    <thead>
                      <tr style={{ borderBottom:'1px solid rgba(255,255,255,0.15)', color:'rgba(255,255,255,0.45)', textAlign:'left' }}>
                        {['Username','Email','Verified','Role','Plan','Subscribed','CC','Logins','Last Login','Last IP','Joined'].map(h => (
                          <th key={h} style={{ padding:'8px 10px', fontWeight:'700', whiteSpace:'nowrap' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {subscribers.map((u, i) => {
                        const isRecent = (u.last_login || '') >= sevenAgo;
                        return (
                          <tr key={i} style={{ borderBottom:'1px solid rgba(255,255,255,0.06)', background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent' }}>
                            <td style={{ padding:'8px 10px', color:'#c4b5fd', fontWeight:'600', whiteSpace:'nowrap' }}>{u.username || '—'}</td>
                            <td style={{ padding:'8px 10px', color:'rgba(255,255,255,0.65)', maxWidth:'180px', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{u.email}</td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap' }}>
                              <span style={{ color: u.email_verified ? '#34d399' : '#fbbf24' }}>
                                {u.email_verified ? '✅' : '⏳'}
                              </span>
                            </td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap' }}>
                              <span style={{ color: u.role === 'admin' ? '#a78bfa' : u.role === 'vip' ? '#f59e0b' : u.role === 'premium' ? '#34d399' : 'rgba(255,255,255,0.35)', fontWeight: ['admin','vip','premium'].includes(u.role) ? '700' : '400' }}>
                                {u.role === 'admin' ? '⚙️ Admin' : u.role === 'vip' ? '👑 VIP' : u.role === 'premium' ? '⭐ Premium' : 'free'}
                              </span>
                            </td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap' }}>
                              <div style={{ display:'flex', gap:'6px', alignItems:'center' }}>
                                <select
                                  value={subscriberTierDrafts[u.email] || (u.subscription_tier || u.role || 'free')}
                                  onChange={(e) => setSubscriberTierDrafts(prev => ({ ...prev, [u.email]: e.target.value }))}
                                  disabled={!!subscriberRoleSaving[u.email]}
                                  style={{ background:'rgba(15,23,42,0.9)', color:'#e2e8f0', border:'1px solid rgba(148,163,184,0.35)', borderRadius:'6px', padding:'4px 6px', fontSize:'12px' }}
                                >
                                  <option value="free">Free</option>
                                  <option value="premium">Premium</option>
                                  <option value="vip">VIP</option>
                                </select>
                                <button
                                  onClick={() => saveSubscriberTier(u.email)}
                                  disabled={!!subscriberRoleSaving[u.email] || (subscriberTierDrafts[u.email] || (u.subscription_tier || u.role || 'free')) === (u.subscription_tier || u.role || 'free')}
                                  style={{ background:'linear-gradient(135deg,#334155,#1e293b)', color:'#f8fafc', border:'1px solid rgba(148,163,184,0.35)', borderRadius:'6px', padding:'4px 8px', fontSize:'11px', fontWeight:'700', cursor:'pointer', opacity: (!!subscriberRoleSaving[u.email] ? 0.6 : 1) }}
                                >
                                  {subscriberRoleSaving[u.email] ? 'Saving...' : 'Save'}
                                </button>
                              </div>
                            </td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap', textAlign:'center' }}>
                              {u.stripe_subscription_id && u.subscription_status === 'active'
                                ? <span title={`${u.subscription_tier || ''} · ${u.stripe_subscription_id}`} style={{ color:'#34d399', fontWeight:'700', fontSize:'13px' }}>✅</span>
                                : <span style={{ color:'rgba(255,255,255,0.2)' }}>—</span>}
                            </td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap', textAlign:'center' }}>
                              {u.stripe_customer_id
                                ? <span title={u.stripe_customer_id} style={{ fontSize:'15px' }}>💳</span>
                                : <span style={{ color:'rgba(255,255,255,0.2)' }}>—</span>}
                            </td>
                            <td style={{ padding:'8px 10px', color:'rgba(255,255,255,0.55)', textAlign:'center' }}>{u.login_count || 0}</td>
                            <td style={{ padding:'8px 10px', whiteSpace:'nowrap' }}>
                              <span style={{ color: isRecent ? '#34d399' : 'rgba(255,255,255,0.4)', fontWeight: isRecent ? '600' : '400' }}>
                                {fmtDate(u.last_login, true)}
                              </span>
                            </td>
                            <td style={{ padding:'8px 10px', color:'rgba(255,255,255,0.45)', whiteSpace:'nowrap', fontFamily:'monospace', fontSize:'11px' }}>{u.last_ip || '—'}</td>
                            <td style={{ padding:'8px 10px', color:'rgba(255,255,255,0.35)', whiteSpace:'nowrap' }}>{fmtDate(u.joined_at)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            );
          })()}
        </div>
      )}

      {activeSection === 'analytics' && (
        <div>
          <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0', marginBottom:'4px' }}>📈 Site Analytics</div>
          <div style={{ fontSize:'13px', color:'rgba(255,255,255,0.45)', marginBottom:'18px' }}>
            Live GA4 reporting is pulled from the Analytics Data API and refreshes on demand inside the admin panel.
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))', gap:'12px', marginBottom:'16px' }}>
            <div style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.10)', borderRadius:'10px', padding:'16px' }}>
              <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.45)', marginBottom:'6px' }}>Measurement ID</div>
              <div style={{ fontSize:'20px', fontWeight:'800', color:'#34d399' }}>{gaMeasurementId}</div>
              <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.5)', marginTop:'6px' }}>This is the GA4 web stream ID used by the frontend.</div>
            </div>
            <div style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.10)', borderRadius:'10px', padding:'16px' }}>
              <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.45)', marginBottom:'6px' }}>Tracked Events</div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:'8px' }}>
                {trackedEvents.map((eventName) => (
                  <span key={eventName} style={{ background:'rgba(99,102,241,0.14)', border:'1px solid rgba(99,102,241,0.28)', borderRadius:'999px', padding:'5px 10px', fontSize:'12px', color:'#c4b5fd' }}>
                    {eventName}
                  </span>
                ))}
              </div>
              <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.5)', marginTop:'10px' }}>Page views, pricing views, sign-up clicks, checkout starts, and successful subscriptions.</div>
            </div>
          </div>

          <div style={{ display:'flex', gap:'10px', flexWrap:'wrap', marginBottom:'16px' }}>
            <a href="https://analytics.google.com/" target="_blank" rel="noreferrer" style={{ textDecoration:'none', background:'linear-gradient(135deg,#2563eb,#1d4ed8)', borderRadius:'8px', padding:'10px 16px', color:'white', fontSize:'13px', fontWeight:'800' }}>Open Google Analytics</a>
            <a href="https://tagmanager.google.com/" target="_blank" rel="noreferrer" style={{ textDecoration:'none', background:'rgba(255,255,255,0.07)', border:'1px solid rgba(255,255,255,0.14)', borderRadius:'8px', padding:'10px 16px', color:'rgba(255,255,255,0.85)', fontSize:'13px', fontWeight:'700' }}>Open Tag Manager</a>
          </div>

          {analyticsLoading ? (
            <div style={{ padding:'18px', borderRadius:'10px', background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)', color:'rgba(255,255,255,0.55)' }}>Loading GA4 summary…</div>
          ) : analyticsMsg ? (
            <div style={{ padding:'14px 16px', borderRadius:'10px', background: analyticsMsg.ok ? 'rgba(5,150,105,0.1)' : 'rgba(248,113,113,0.12)', border:`1px solid ${analyticsMsg.ok ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.35)'}`, color: analyticsMsg.ok ? '#34d399' : '#f87171', marginBottom:'16px' }}>
              {analyticsMsg.text}
            </div>
          ) : null}

          {analyticsSummary?.configured && analyticsSummary.summary ? (
            <>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))', gap:'10px', marginBottom:'16px' }}>
                {[
                  { label:'Active users (7d)', value: analyticsSummary.summary.last_7_days?.activeUsers ?? 0, color:'#34d399' },
                  { label:'Sessions (7d)', value: analyticsSummary.summary.last_7_days?.sessions ?? 0, color:'#93c5fd' },
                  { label:'Page views (7d)', value: analyticsSummary.summary.last_7_days?.screenPageViews ?? 0, color:'#fbbf24' },
                  { label:'Active users (30d)', value: analyticsSummary.summary.last_30_days?.activeUsers ?? 0, color:'#a78bfa' },
                  { label:'Sessions (30d)', value: analyticsSummary.summary.last_30_days?.sessions ?? 0, color:'#f97316' },
                ].map(card => (
                  <div key={card.label} style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px', padding:'12px', textAlign:'center' }}>
                    <div style={{ fontSize:'22px', fontWeight:'900', color: card.color }}>{Number(card.value || 0).toLocaleString('en-GB')}</div>
                    <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'2px' }}>{card.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'10px', padding:'16px' }}>
                <div style={{ fontSize:'12px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.45)', marginBottom:'12px' }}>Tracked actions in the last 7 days</div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))', gap:'10px' }}>
                  {trackedEvents.filter(eventName => eventName !== 'page_view').map((eventName) => {
                    const count = analyticsSummary.summary.events_last_7_days?.[eventName] ?? 0;
                    return (
                      <div key={eventName} style={{ border:'1px solid rgba(255,255,255,0.08)', borderRadius:'8px', padding:'12px', background:'rgba(15,23,42,0.5)' }}>
                        <div style={{ fontSize:'20px', fontWeight:'900', color:'#c4b5fd' }}>{Number(count || 0).toLocaleString('en-GB')}</div>
                        <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>{eventName}</div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ marginTop:'12px', fontSize:'12px', color:'rgba(255,255,255,0.45)' }}>
                  Reporting source: {analyticsSummary.credential_source || 'unknown'} · Property: {analyticsSummary.property_id || '—'}
                </div>
              </div>
            </>
          ) : null}

          {analyticsSummary?.selection_guardrails && (
            <div style={{ marginTop:'14px', background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'10px', padding:'16px' }}>
              <div style={{ fontSize:'12px', textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.45)', marginBottom:'12px' }}>Live Pick Guardrails (Today)</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))', gap:'10px' }}>
                {[
                  { label:'Evaluated candidates', value: analyticsSummary.selection_guardrails.evaluated_official_candidates ?? 0, color:'#93c5fd' },
                  { label:'Blocked by coverage', value: analyticsSummary.selection_guardrails.blocked_by_coverage ?? 0, color:'#fbbf24' },
                  { label:'Blocked by high NR improver', value: analyticsSummary.selection_guardrails.blocked_by_high_nr_improver ?? 0, color:'#f87171' },
                ].map(card => (
                  <div key={card.label} style={{ border:'1px solid rgba(255,255,255,0.08)', borderRadius:'8px', padding:'12px', background:'rgba(15,23,42,0.5)' }}>
                    <div style={{ fontSize:'20px', fontWeight:'900', color: card.color }}>{Number(card.value || 0).toLocaleString('en-GB')}</div>
                    <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', marginTop:'4px' }}>{card.label}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop:'10px', fontSize:'12px', color:'rgba(255,255,255,0.45)' }}>
                Refreshed at: {analyticsSummary.selection_guardrails.as_of || '—'}
              </div>
            </div>
          )}

          {!analyticsLoading && analyticsSummary && !analyticsSummary.configured && (
            <div style={{ marginTop:'16px', padding:'14px 16px', borderRadius:'10px', background:'rgba(245,158,11,0.12)', border:'1px solid rgba(245,158,11,0.3)', color:'#fbbf24' }}>
              GA4 reporting is not connected yet. Add the GA4 property ID plus service account credentials to enable live visitor and conversion counts here.
            </div>
          )}
        </div>
      )}

      {activeSection === 'majoranalysis' && (
        <div>
          <div style={{ fontSize:'16px', fontWeight:'700', color:'#e2e8f0', marginBottom:'16px' }}>🏆 Major Races AI Analysis</div>
          <p style={{ fontSize:'13px', color:'rgba(255,255,255,0.55)', marginBottom:'16px' }}>
            Run the early-bird analysis for all upcoming major races. This scrapes ante-post markets from Sporting Life, scores each horse, and picks the top contender per race. Scheduled daily at 07:00 UTC via Step Functions.
          </p>
          <button
            disabled={majorRunning}
            onClick={() => {
              setMajorRunning(true);
              setMajorMsg(null);
              fetch(`${API_BASE_URL}/api/major-race-analysis/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'x-admin-token': adminToken },
              })
                .then(r => r.json())
                .then(d => {
                  if (d.success) {
                    setMajorMsg({ ok: true, text: `✅ ${d.message}. Refresh the Major Races page to see results.` });
                  } else {
                    setMajorMsg({ ok: false, text: `❌ ${d.error || 'Analysis failed'}` });
                  }
                })
                .catch(e => setMajorMsg({ ok: false, text: `❌ Network error: ${e.message}` }))
                .finally(() => setMajorRunning(false));
            }}
            style={{
              padding:'12px 28px', borderRadius:'10px', border:'none', cursor: majorRunning ? 'not-allowed' : 'pointer',
              background: majorRunning ? 'rgba(124,58,237,0.3)' : 'linear-gradient(135deg,#7c3aed,#6366f1)',
              color:'white', fontSize:'14px', fontWeight:'700', transition:'all 0.2s',
            }}
          >
            {majorRunning ? '⏳ Running analysis…' : '🚀 Run Daily Analysis Now'}
          </button>
          {majorMsg && (
            <div style={{ marginTop:'16px', padding:'12px 16px', borderRadius:'8px', background: majorMsg.ok ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)', border: `1px solid ${majorMsg.ok ? 'rgba(52,211,153,0.4)' : 'rgba(248,113,113,0.4)'}`, color: majorMsg.ok ? '#34d399' : '#f87171', fontSize:'14px' }}>
              {majorMsg.text}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function _formatRaceTime(rt) {
  if (!rt) return { date: '', time: '' };
  const m = rt.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})/);
  if (m) {
    const d = new Date(`${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}T${m[4].padStart(2,'0')}:${m[5]}:00Z`);
    const tz = { timeZone: 'Europe/Dublin' };
    return {
      date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', year:'numeric', ...tz }),
      time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12: false, ...tz }),
    };
  }
  const isoM = rt.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
  if (isoM) {
    const [, datePart] = isoM;
    try {
      const d = new Date(rt.endsWith('Z') || rt.includes('+') ? rt : rt + 'Z');
      const tz = { timeZone: 'Europe/Dublin' };
      return {
        date: d.toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', year:'numeric', ...tz }),
        time: d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', hour12: false, ...tz }),
      };
    } catch { return { date: datePart, time: rt.substring(11, 16) }; }
  }
  return { date: rt.substring(0,10), time: rt.substring(11,16) };
}

function LossAnalysisPanel({ picks }) {
  const [learningStatus, setLearning] = useState({ state: 'idle', message: '', changes: {} });

  const nonWins = (picks || []).filter(p => {
    const re = p.result_emoji
      || (p.outcome === 'loss'   || p.outcome === 'LOSS'   || p.outcome === 'LOST'   ? 'LOSS'
        : p.outcome === 'placed' || p.outcome === 'PLACED'                           ? 'PLACED'
        : null);
    return re === 'LOSS' || re === 'PLACED';
  });

  const SCORE_LABELS_MAP = {
    going_suitability:'Going Suitability', recent_win:'Last Race Win', total_wins:'Form Wins',
    form:'Recent Form', form_score:'Recent Form', sweet_spot:'Odds Sweet Spot',
    consistency:'Consistency', course_performance:'C&D Wins', cd_bonus:'C&D Bonus',
    trainer_strike_rate:'Trainer Strike Rate', meeting_focus_trainer:'Trainer @ Meeting',
    jockey_quality:'Jockey Quality', database_history:'DB History', age_factor:'Age Factor',
  };

  const applyLearning = async () => {
    setLearning({ state: 'loading', message: 'Analysing missed winners and updating model weights…', changes: {} });
    try {
      const res  = await fetch(API_BASE_URL + '/api/learning/apply', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({}) });
      const data = await res.json();
      if (data.success) {
        setLearning({ state: 'done', message: data.message, changes: data.changes || {} });
      } else {
        setLearning({ state: 'error', message: data.error || 'Unknown error', changes: {} });
      }
    } catch (e) {
      setLearning({ state: 'error', message: 'Network error: ' + e.message, changes: {} });
    }
  };

  if (nonWins.length === 0) {
    return (
      <div style={{ textAlign:'center', padding:'40px', color:'rgba(255,255,255,0.35)', fontSize:'14px' }}>
        {picks.length === 0 ? 'No results loaded yet.' : '✅ No losses or placed picks in the current result set.'}
      </div>
    );
  }

  return (
    <div>
      {/* Systemic pattern summary */}
      {(() => {
        const patterns = [];
        const jockeyZero    = nonWins.filter(p => parseFloat((p.score_breakdown||{}).jockey_quality||0) === 0).length;
        const dbZero        = nonWins.filter(p => parseFloat((p.score_breakdown||{}).database_history||0) === 0).length;
        const unknownTrn    = nonWins.filter(p => parseFloat((p.score_breakdown||{}).unknown_trainer_penalty||0) < 0).length;
        const bottomWinners = nonWins.filter(p => {
          const fld = [...(p.all_horses||[])].sort((a,b)=>parseFloat(b.score||0)-parseFloat(a.score||0));
          if (fld.length < 3) return false;
          const wn = (p.result_winner_name||'').toLowerCase();
          const wi = fld.findIndex(h=>(h.horse||'').toLowerCase()===wn);
          return wi !== -1 && wi >= Math.ceil(fld.length / 2);
        }).length;
        const bigField = nonWins.filter(p => {
          const m = (p.result_analysis||'').match(/of (\d+)/);
          return m && parseInt(m[1]) >= 16;
        }).length;
        if (jockeyZero === nonWins.length)
          patterns.push({ icon:'🏇', col:'#93c5fd', title:'Jockey scoring inactive', detail:`${jockeyZero}/${nonWins.length} picks scored 0 for jockey quality — strong jockey bookings, course specialists and first-time big-stable rides are not factored in at all` });
        if (dbZero === nonWins.length)
          patterns.push({ icon:'📂', col:'#fbbf24', title:'No historical database data', detail:`${dbZero}/${nonWins.length} picks had zero DB history score — the model has no recorded win-rate data for any of these horses at this course/distance combination` });
        if (unknownTrn > 0)
          patterns.push({ icon:'❓', col:'#f97316', title:`Unknown trainer penalty insufficient`, detail:`${unknownTrn}/${nonWins.length} picks received -8pts unknown trainer penalty yet were still selected — if the trainer has no verified track record, selection confidence should be reduced further` });
        if (bottomWinners > 0)
          patterns.push({ icon:'📉', col:'#f87171', title:`Winner ranked bottom half of field`, detail:`${bottomWinners} race${bottomWinners>1?'s':''} won by a horse ranked in the bottom half of our model — winner likely had limited form data or first run at this trip/going; low model score ≠ no chance` });
        if (bigField > 0)
          patterns.push({ icon:'🎲', col:'#a78bfa', title:`Large-field handicap risk`, detail:`${bigField} race${bigField>1?'s':''} run in fields of 16+ runners — big handicaps carry inherent chaos; pace, draw and luck have outsized influence the model cannot capture` });
        if (patterns.length === 0) return null;
        return (
          <div style={{ background:'rgba(30,58,95,0.35)', border:'1px solid rgba(59,130,246,0.3)', borderRadius:'10px', padding:'16px 20px', marginBottom:'20px' }}>
            <div style={{ fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px', color:'#93c5fd', marginBottom:'12px', fontWeight:'800' }}>🔬 Systemic Patterns Found in These Losses</div>
            <div style={{ display:'flex', flexDirection:'column', gap:'10px' }}>
              {patterns.map((pt, pi) => (
                <div key={pi} style={{ display:'flex', gap:'10px', alignItems:'flex-start' }}>
                  <span style={{ fontSize:'15px', flexShrink:0, lineHeight:'1.3' }}>{pt.icon}</span>
                  <div>
                    <div style={{ fontWeight:'700', color:pt.col, fontSize:'13px', marginBottom:'2px' }}>{pt.title}</div>
                    <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.55)', lineHeight:1.5 }}>{pt.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {nonWins.map((pick, idx) => {
        const sb       = pick.score_breakdown || {};
        const odds     = parseFloat(pick.odds || 0);
        const score    = parseFloat(pick.comprehensive_score || pick.analysis_score || 0);
        const winner   = pick.result_winner_name || pick.winner_name || '?';
        const ft       = _formatRaceTime(pick.race_time);
        const wa       = (() => {
          const stored = pick.winner_analysis || {};
          if (stored.winner_found) return stored;
          const field = [...(pick.all_horses || [])]
            .map(h => ({ ...h, score: parseFloat(h.score || 0), odds: parseFloat(h.odds || 0) }))
            .sort((a, b) => b.score - a.score);
          const winnerName = (pick.result_winner_name || pick.winner_name || '').toLowerCase();
          if (!winnerName || field.length === 0) return stored;
          const winnerIdx = field.findIndex(h => (h.horse || '').toLowerCase() === winnerName);
          if (winnerIdx === -1) return stored;
          const winnerH  = field[winnerIdx];
          const gap      = score - winnerH.score;
          const why      = [];
          if (winnerIdx === 0) {
            why.push(`${winnerH.horse} also ranked #1 in our model — race was a genuine toss-up on paper`);
          } else {
            why.push(`${winnerH.horse} ranked #${winnerIdx + 1} of ${field.length} in our model (score ${winnerH.score.toFixed(0)}) — model over-favoured our pick by ${gap.toFixed(0)}pts`);
          }
          if (winnerH.score < 35) why.push(`Winner score only ${winnerH.score.toFixed(0)}/100 — likely limited UK/IE recorded form in our database; unproven horses can still win`);
          if (parseFloat(sb.unknown_trainer_penalty || 0) < 0) why.push(`Unknown trainer penalty (-${Math.abs(parseFloat(sb.unknown_trainer_penalty)).toFixed(0)}pts) applied to our pick but score still high enough to select — trainer track record absent`);
          if (parseFloat(sb.going_suitability || 0) >= 16) why.push(`Going Suitability scored +${parseFloat(sb.going_suitability).toFixed(0)}pts — may be over-weighted vs actual ground impact on the day`);
          if (winnerH.odds > 8) why.push(`Winner was ${toFractional(winnerH.odds)} — market also underestimated them; race pace or trainer booking likely key`);
          return {
            winner_found: true,
            winner_name: winnerH.horse,
            winner_score: winnerH.score.toFixed(0),
            winner_rank: winnerIdx + 1,
            winner_rank_of: field.length,
            winner_odds_fractional: winnerH.odds > 1 ? toFractional(winnerH.odds) : '?',
            score_gap: gap,
            why_missed: why,
          };
        })();
        const isPlaced = (pick.result_emoji || pick.outcome || '').toUpperCase().includes('PLACED');
        const topBreakdown = Object.entries(sb)
          .filter(([,v]) => parseFloat(v) > 0)
          .sort(([,a],[,b]) => parseFloat(b) - parseFloat(a))
          .slice(0, 5);

        return (
          <div key={idx} style={{ background:'#1a1a2e', border:`1px solid ${isPlaced ? 'rgba(59,130,246,0.4)' : 'rgba(239,68,68,0.4)'}`, borderRadius:'12px', padding:'20px 24px', marginBottom:'18px', borderLeft:`4px solid ${isPlaced ? '#3b82f6' : '#ef4444'}` }}>

            {/* Header row */}
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'8px', marginBottom:'16px' }}>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:'18px', fontWeight:'800', color:'white' }}>
                  {isPlaced ? '🥈' : '✗'} {pick.horse}
                  <span style={{ marginLeft:'8px', fontSize:'12px', fontWeight:'600', color: isPlaced ? '#60a5fa' : '#f87171' }}>{isPlaced ? 'PLACED' : 'LOSS'}</span>
                  <span style={{ marginLeft:'8px', fontSize:'11px', color:'rgba(255,255,255,0.35)' }}>{pick._dayLabel}</span>
                </div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.5)', marginTop:'3px' }}>
                  {ft.time} · {pick.course}
                  &nbsp;·&nbsp;Our score: <strong style={{color:'white'}}>{score.toFixed(0)}/100</strong>
                  &nbsp;·&nbsp;Odds: <strong style={{color:'#93c5fd'}}>{(odds-1).toFixed(0)}/1</strong>
                </div>
              </div>
              {(pick.result_analysis || winner !== '?') && (
                <div style={{ background: isPlaced ? 'rgba(59,130,246,0.2)' : 'rgba(239,68,68,0.2)', border:`1px solid ${isPlaced ? 'rgba(59,130,246,0.45)' : 'rgba(239,68,68,0.45)'}`, color: isPlaced ? '#93c5fd' : '#fca5a5', borderRadius:'7px', padding:'6px 12px', fontSize:'11px', fontWeight:'700', lineHeight:1.5, textAlign:'right', flexShrink:0 }}>
                  {pick.result_analysis || (winner !== '?' ? `Winner: ${winner}` : 'Result recorded')}
                </div>
              )}
            </div>

            {/* Winner comparison */}
            {wa.winner_found && (
              <div style={{ background:'rgba(255,255,255,0.06)', borderRadius:'10px', padding:'14px 16px', marginBottom:'16px' }}>
                <div style={{ fontSize:'10px', fontWeight:'800', color:'#fbbf24', textTransform:'uppercase', letterSpacing:'1px', marginBottom:'12px' }}>🏆 Winner Comparison — {wa.winner_name}</div>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px', marginBottom:'12px' }}>
                  <div style={{ background:'rgba(239,68,68,0.12)', borderRadius:'8px', padding:'10px 12px', border:'1px solid rgba(239,68,68,0.25)' }}>
                    <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', marginBottom:'4px', textTransform:'uppercase', letterSpacing:'0.8px' }}>Our Pick</div>
                    <div style={{ fontWeight:'800', color:'white', fontSize:'14px' }}>{pick.horse}</div>
                    <div style={{ fontSize:'20px', fontWeight:'900', color:'#f87171', marginTop:'4px' }}>{score.toFixed(0)}<span style={{fontSize:'11px',fontWeight:'500',color:'rgba(255,255,255,0.4)'}}>/100</span></div>
                    <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'2px' }}>Ranked #1 in field · {(odds-1).toFixed(0)}/1</div>
                  </div>
                  <div style={{ background:'rgba(16,185,129,0.12)', borderRadius:'8px', padding:'10px 12px', border:'1px solid rgba(16,185,129,0.25)' }}>
                    <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.45)', marginBottom:'4px', textTransform:'uppercase', letterSpacing:'0.8px' }}>Actual Winner</div>
                    <div style={{ fontWeight:'800', color:'white', fontSize:'14px' }}>{wa.winner_name}</div>
                    <div style={{ fontSize:'20px', fontWeight:'900', color:'#34d399', marginTop:'4px' }}>{wa.winner_score}<span style={{fontSize:'11px',fontWeight:'500',color:'rgba(255,255,255,0.4)'}}>/100</span></div>
                    <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginTop:'2px' }}>Ranked #{wa.winner_rank} of {wa.winner_rank_of} · {wa.winner_odds_fractional}</div>
                  </div>
                </div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.45)', marginBottom:'6px' }}>
                  Model gap: <strong style={{color: wa.score_gap > 10 ? '#fbbf24' : '#a3a3a3'}}>{wa.score_gap > 0 ? '+' : ''}{wa.score_gap} pts</strong> in favour of our pick
                </div>
                {(wa.why_missed || []).map((reason, ri) => (
                  <div key={ri} style={{ display:'flex', gap:'7px', alignItems:'flex-start', marginTop:'6px' }}>
                    <span style={{ color:'#fbbf24', flexShrink:0, marginTop:'1px' }}>›</span>
                    <span style={{ fontSize:'12px', color:'rgba(255,255,255,0.65)', lineHeight:1.5 }}>{reason}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Score breakdown */}
            {topBreakdown.length > 0 && (
              <div>
                <div style={{ fontSize:'10px', fontWeight:'800', color:'#f59e0b', textTransform:'uppercase', letterSpacing:'1px', marginBottom:'8px' }}>📊 What inflated our score</div>
                {topBreakdown.map(([k, v], bi) => {
                  const pts    = parseFloat(v);
                  const pct    = score > 0 ? pts / score * 100 : 0;
                  const isHigh = k === 'going_suitability' || pts > 22;
                  const label  = SCORE_LABELS_MAP[k] || k.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
                  return (
                    <div key={bi} style={{ marginBottom:'7px' }}>
                      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'3px' }}>
                        <span style={{ fontSize:'11px', color: isHigh ? '#fbbf24' : 'rgba(255,255,255,0.5)' }}>{isHigh ? '⚠️ ' : ''}{label}</span>
                        <span style={{ fontSize:'11px', fontWeight:'700', color: isHigh ? '#fbbf24' : '#93c5fd' }}>+{pts.toFixed(0)} pts ({pct.toFixed(0)}%)</span>
                      </div>
                      <div style={{ background:'rgba(255,255,255,0.08)', borderRadius:'3px', height:'5px', overflow:'hidden' }}>
                        <div style={{ width:`${Math.min(pct,100)}%`, height:'100%', background: isHigh ? '#f59e0b' : '#3b82f6', borderRadius:'3px' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* Apply Learning */}
      <div style={{ background:'rgba(16,185,129,0.08)', border:'1px solid rgba(16,185,129,0.3)', borderRadius:'12px', padding:'20px 24px' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'12px', marginBottom: learningStatus.state !== 'idle' ? '16px' : '0' }}>
          <div>
            <div style={{ fontSize:'13px', fontWeight:'800', color:'#34d399', marginBottom:'4px' }}>🧠 Auto-Update Model Weights</div>
            <div style={{ fontSize:'12px', color:'rgba(255,255,255,0.5)', lineHeight:1.5 }}>
              Analyses every missed winner above and nudges the scoring weights in DynamoDB so tomorrow's picks improve.
            </div>
          </div>
          <button
            onClick={applyLearning}
            disabled={learningStatus.state === 'loading'}
            style={{ background: learningStatus.state === 'done' ? '#059669' : '#1d4ed8', border:'none', borderRadius:'8px', color:'white', padding:'10px 20px', cursor: learningStatus.state === 'loading' ? 'not-allowed' : 'pointer', fontWeight:'700', fontSize:'13px', opacity: learningStatus.state === 'loading' ? 0.7 : 1, flexShrink:0, whiteSpace:'nowrap' }}
          >
            {learningStatus.state === 'loading' ? '⏳ Updating…' : learningStatus.state === 'done' ? '✅ Applied' : '⚡ Apply Learning Now'}
          </button>
        </div>
        {learningStatus.state === 'done' && (
          <div>
            <div style={{ fontSize:'12px', color:'#34d399', marginBottom:'10px', fontWeight:'700' }}>{learningStatus.message}</div>
            {Object.keys(learningStatus.changes).length > 0 && (
              <div style={{ display:'flex', flexWrap:'wrap', gap:'8px' }}>
                {Object.entries(learningStatus.changes).map(([factor, ch]) => (
                  <div key={factor} style={{ background:'rgba(255,255,255,0.07)', borderRadius:'6px', padding:'5px 10px', fontSize:'11px' }}>
                    <span style={{ color:'rgba(255,255,255,0.5)', textTransform:'capitalize' }}>{factor.replace(/_/g,' ')}</span>
                    <span style={{ marginLeft:'6px', fontWeight:'800', color: ch.nudge > 0 ? '#34d399' : '#f87171' }}>
                      {ch.from.toFixed(1)} → {ch.to.toFixed(1)} ({ch.nudge > 0 ? '+' : ''}{ch.nudge.toFixed(2)})
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {learningStatus.state === 'error' && (
          <div style={{ fontSize:'12px', color:'#f87171', marginTop:'8px' }}>⚠️ {learningStatus.message}</div>
        )}
      </div>
    </div>
  );
}

function AdminSliderRow({ label, desc, value, defaultValue, min, max, step, penalty, onChange }) {
  const numVal = parseFloat(value) || 0;
  const pct    = max > min ? ((numVal - min) / (max - min)) * 100 : 0;
  const isChanged = numVal !== (parseFloat(defaultValue) || 0);
  const accentColor = penalty ? '#f87171' : '#a78bfa';

  return (
    <div style={{ background:'rgba(255,255,255,0.04)', border:`1px solid ${isChanged ? (penalty ? 'rgba(248,113,113,0.4)' : 'rgba(167,139,250,0.4)') : 'rgba(255,255,255,0.1)'}`, borderRadius:'10px', padding:'12px 14px' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom:'6px' }}>
        <div>
          <span style={{ fontSize:'13px', fontWeight:'600', color: isChanged ? accentColor : 'rgba(255,255,255,0.85)' }}>{label}</span>
          {isChanged && <span style={{ marginLeft:'6px', fontSize:'11px', color:'rgba(255,255,255,0.4)' }}>(was {defaultValue})</span>}
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:'6px' }}>
          <input
            type="number"
            value={numVal}
            min={min} max={max} step={step}
            onChange={e => onChange(parseFloat(e.target.value) || 0)}
            style={{ width:'56px', background:'rgba(0,0,0,0.3)', border:`1px solid ${accentColor}40`, borderRadius:'5px', color:'white', padding:'2px 6px', fontSize:'13px', fontWeight:'700', textAlign:'center' }}
          />
          {penalty && <span style={{ fontSize:'11px', color:'rgba(248,113,113,0.6)' }}>pts</span>}
          {!penalty && <span style={{ fontSize:'11px', color:'rgba(167,139,250,0.6)' }}>pts</span>}
        </div>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={numVal}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width:'100%', accentColor, cursor:'pointer' }}
      />
      <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.35)', marginTop:'3px' }}>{desc}</div>
    </div>
  );
}

export default App;

