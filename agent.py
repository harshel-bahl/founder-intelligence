#!/usr/bin/env python3

import os
import re
import time
import json
import requests
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError as TenacityRetryError

# -------------------- Configuration --------------------

def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default

def env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return default

# -------------------- URL Processing --------------------

def sanitize_urls(text: str) -> List[str]:
    urls = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "linkedin.com/in/" in line:
            urls.append(line)
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped

def extract_name_from_linkedin(url: str) -> str:
    try:
        slug = url.split("linkedin.com/in/")[1].strip("/")
        slug = slug.split("?")[0]
        slug = slug.replace("%20", " ").replace("-", " ").replace("_", " ")
        slug = " ".join([t for t in slug.split() if not any(c.isdigit() for c in t)])
        return " ".join([w.capitalize() for w in slug.split() if w]).strip()
    except Exception:
        return ""

def domain_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse
    except Exception:
        return ""
    try:
        netloc = urlparse(url).netloc
        return netloc.replace("www.", "")
    except Exception:
        return ""

# -------------------- Web Fetching --------------------

DEFAULT_HEADERS = {
    "User-Agent": os.environ.get(
        "LINKEDIN_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def linkedin_cookies() -> dict:
    li_at = os.environ.get("LINKEDIN_LI_AT", "").strip()
    return {"li_at": li_at} if li_at else {}

def fetch_url(url: str, timeout: int = 15) -> Tuple[Optional[str], int, str]:
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, cookies=linkedin_cookies(), timeout=timeout)
        if r.status_code == 200 and r.text:
            return r.text, 200, "ok"
        return None, r.status_code, f"http_status_{r.status_code}"
    except requests.RequestException as e:
        return None, 0, f"request_error:{e}"

def visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    og_desc = ""
    og = soup.find("meta", {"property": "og:description"})
    if og and og.get("content"):
        og_desc = og["content"]
    text = soup.get_text(separator="\n")
    combined = f"{og_desc}\n{text}"
    combined = re.sub(r"[ \t]+", " ", combined)
    combined = re.sub(r"\n{2,}", "\n", combined)
    return combined.strip()

# -------------------- SerpAPI Integration --------------------

SERP_API_URL = "https://serpapi.com/search.json"

def serp_key_required() -> str:
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing SERPAPI_API_KEY")
    return key

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
def serp_search(query: str, num: int = 5, engine: str = "google") -> List[Dict]:
    params = {
        "engine": engine,
        "q": query,
        "api_key": serp_key_required(),
        "num": num,
        "hl": "en"
    }
    resp = requests.get(SERP_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("organic_results", []):
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source_domain": domain_from_url(item.get("link", "")),
            "query": query
        })
    return results

def dedupe_links(items: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for it in items:
        link = it.get("link")
        if not link or link in seen: 
            continue
        seen.add(link)
        out.append(it)
    return out

# -------------------- Search Queries --------------------

ENTREPRENEUR_QUERIES = [
    "{name} founder cofounder startup venture round site:linkedin.com OR site:crunchbase.com OR site:angel.co",
    "{name} CEO CTO founder raised seed series A site:techcrunch.com OR site:crunchbase.com",
    "{name} YC Y Combinator accelerator Techstars site:yc.com OR site:news.ycombinator.com",
    "{name} stealth startup site:linkedin.com/in OR site:twitter.com OR site:x.com",
    "{name} dropout OR left college OR left university OR leave of absence",
    "{name} left MIT OR left Stanford OR left Harvard OR dropped out of MIT",
    "{name} quant OR trading to startup OR founder OR switched fields",
]

DISCOVERY_QUERIES = [
    "{name} blog OR newsletter OR substack OR medium OR mirror.xyz OR ghost.io OR wordpress OR notion site:substack.com OR site:medium.com OR site:mirror.xyz OR site:ghost.io OR site:wordpress.com OR site:github.io OR site:notion.site",
    "{name} personal website OR portfolio OR about me",
    "{name} site:github.io OR site:itch.io OR site:dev.to",
    "{name} site:x.com OR site:twitter.com",
]

# -------------------- Evidence Collection --------------------

def collect_entrepreneur_evidence(name: str, results_per_query: int, passes: int) -> Tuple[List[Dict], List[Dict]]:
    queries = ENTREPRENEUR_QUERIES[:]
    queries = queries[: passes * 3]
    trav, results = [], []
    for q in queries:
        query = q.format(name=name)
        trav.append({"action": "serp_search", "query": query})
        try:
            res = serp_search(query, num=results_per_query)
        except Exception as e:
            trav.append({"action": "error", "query": query, "error": str(e)})
            res = []
        results.extend(res)
    results = dedupe_links(results)
    trav.append({"action": "entrepreneur_aggregate", "total_results": len(results)})
    return results, trav

def discover_personal_sources(name: str, results_per_query: int, passes: int) -> Tuple[List[Dict], List[Dict]]:
    queries = DISCOVERY_QUERIES[:]
    queries = queries[: passes * 3]
    trav, urls = [], []
    for q in queries:
        query = q.format(name=name)
        trav.append({"action": "serp_discovery", "query": query})
        try:
            res = serp_search(query, num=results_per_query)
        except Exception as e:
            trav.append({"action": "error", "query": query, "error": str(e)})
            res = []
        urls.extend(res)
    urls = dedupe_links(urls)
    trav.append({"action": "discovery_aggregate", "total_results": len(urls)})
    return urls, trav

def fetch_and_snippet(url: str, max_chars: int = 1200) -> Optional[Dict]:
    html, status, note = fetch_url(url)
    if not html:
        return None
    text = visible_text_from_html(html)
    snippet = text[:max_chars].replace("\n", " ").strip()
    title = ""
    try:
        m = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
    except Exception:
        title = ""
    return {
        "query": "direct_fetch",
        "title": title or "Fetched page",
        "link": url,
        "snippet": snippet,
        "source_domain": domain_from_url(url)
    }

def collect_profile_corpus(profile_url: str, name: str, results_per_query: int, passes: int) -> Tuple[List[Dict], List[Dict]]:
    trav = [{"action": "fetch_linkedin", "url": profile_url}]
    html, status, note = fetch_url(profile_url)
    trav.append({"action": "fetch_linkedin_result", "status": status, "note": note})
    corpus = []
    if html:
        text = visible_text_from_html(html)
        trav.append({"action": "linkedin_text_len", "length": len(text)})
        if len(text) > 400:
            corpus.append({
                "query": "linkedin_profile",
                "title": "LinkedIn profile (parsed)",
                "link": profile_url,
                "snippet": text[:1600].replace("\n", " ").strip(),
                "source_domain": "linkedin.com"
            })
    if not corpus or len(corpus[0]["snippet"]) < 400:
        discovered, trav_d = discover_personal_sources(name, results_per_query, passes)
        trav.extend(trav_d)
        fetched_any = 0
        for item in discovered[: 8]:
            page = fetch_and_snippet(item["link"])
            if page and len(page.get("snippet","")) > 400:
                corpus.append(page)
                fetched_any += 1
            if fetched_any >= 5:
                break
        trav.append({"action": "personal_sources_used", "count": fetched_any})
    return corpus, trav

# -------------------- Analysis --------------------

def load_prompt_template() -> str:
    """Load the prompt template from the prompts folder."""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "founder_scoring_prompt.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt template: {e}")

PROMPT_TEMPLATE = load_prompt_template()

def openai_client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai package not installed. `pip install openai`") from e
    
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    
    if not api_key.startswith("sk-"):
        raise RuntimeError(f"Invalid OPENAI_API_KEY format. Should start with 'sk-' but got: '{api_key[:10]}...'")
    
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return client
    except Exception as e:
        raise RuntimeError(f"OpenAI authentication failed. Please check your API key. Error: {str(e)}") from e

def openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

def openai_temp() -> float:
    model = openai_model().lower()

    if "gpt-4o" not in model:
        return 1.0
    return env_float("OPENAI_TEMPERATURE", 0.1)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
def judge_with_llm(profile_url: str, name_guess: str, pages: List[Dict], search_evidence: List[Dict]) -> Dict:
    payload = {
        "pages": pages,
        "search_evidence": search_evidence
    }
    
    try:
        user_msg = PROMPT_TEMPLATE.format(
            profile_url=profile_url,
            name_guess=name_guess,
            evidence_json=json.dumps(payload, ensure_ascii=False)
        )
    except KeyError as e:
        raise RuntimeError(f"Prompt template formatting error - missing placeholder: {e}")
    except Exception as e:
        raise RuntimeError(f"Prompt template formatting error: {e}")
    
    client = openai_client()
    
    try:
        try:
            resp = client.chat.completions.create(
                model=openai_model(),
                temperature=openai_temp(),
                messages=[
                    {"role": "system", "content": "You are an expert talent researcher. Respond with strict JSON only."},
                    {"role": "user", "content": user_msg}
                ],
                response_format={"type": "json_object"}
            )
        except Exception:
            
            resp = client.chat.completions.create(
                model=openai_model(),
                temperature=openai_temp(),
                messages=[
                    {"role": "system", "content": "You are an expert talent researcher. Respond with strict JSON only. Return JSON object, no prose."},
                    {"role": "user", "content": user_msg}
                ]
            )
        
        raw_content = resp.choices[0].message.content
        
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response: {e}. Raw content: {raw_content[:500]}...")
        
        data.setdefault("source_confidence_assessments", [])
        data.setdefault("high_confidence_sources_used", [])
        data.setdefault("entrepreneurial_score", 0.0)
        data.setdefault("contrarian_multiplier", 1.0)
        data.setdefault("final_score", 0.0)
        data.setdefault("entrepreneurial_evidence_points", [])
        data.setdefault("contrarian_evidence_points", [])
        data.setdefault("summary", "")
        data.setdefault("confidence", 0.0)
        
        if data["contrarian_multiplier"] > 1.5:
            data["contrarian_multiplier"] = 1.5
        elif data["contrarian_multiplier"] < 1.0:
            data["contrarian_multiplier"] = 1.0
        
        return data
        
    except Exception as e:
        raise RuntimeError(f"Error in LLM judging for {profile_url}: {str(e)}") from e

# -------------------- Main Analysis Function --------------------

def score_one_profile(profile_url: str, results_per_query: int, passes: int) -> Dict:

    name = extract_name_from_linkedin(profile_url) or profile_url.strip("/").split("/")[-1].replace("-", " ").strip()
    traversal = []
    
    try:
        pages, trav_pages = collect_profile_corpus(profile_url, name, results_per_query, passes)
        traversal.extend(trav_pages)
        
        ent_evidence, trav_ent = collect_entrepreneur_evidence(name, results_per_query, passes)
        traversal.extend(trav_ent)

        llm_result = judge_with_llm(profile_url, name, pages, ent_evidence)

        return {
            "profile_url": profile_url,
            "name_guess": name,
            "entrepreneurial_score": float(llm_result.get("entrepreneurial_score", 0.0)),
            "contrarian_multiplier": float(llm_result.get("contrarian_multiplier", 1.0)),
            "final_score": float(llm_result.get("final_score", 0.0)),
            "summary": llm_result.get("summary", ""),
            "confidence": float(llm_result.get("confidence", 0.0)),
            "entrepreneurial_evidence_points": list(llm_result.get("entrepreneurial_evidence_points", [])),
            "contrarian_evidence_points": list(llm_result.get("contrarian_evidence_points", [])),
            "source_confidence_assessments": list(llm_result.get("source_confidence_assessments", [])),
            "high_confidence_sources_used": list(llm_result.get("high_confidence_sources_used", [])),
            "pages": pages,
            "search_evidence": ent_evidence,
            "traversal_log": traversal
        }
        
    except Exception as e:
        
        root_msg = str(e)
        if isinstance(e, TenacityRetryError):
            try:
                cause = e.last_attempt.exception()
                root_msg = f"{type(cause).__name__}: {cause}"
            except Exception:
                root_msg = str(e)
        return {
            "profile_url": profile_url,
            "name_guess": name,
            "entrepreneurial_score": 0.0,
            "contrarian_multiplier": 1.0,
            "final_score": 0.0,
            "summary": f"Error during analysis: {root_msg}",
            "confidence": 0.0,
            "entrepreneurial_evidence_points": [],
            "contrarian_evidence_points": [],
            "source_confidence_assessments": [],
            "high_confidence_sources_used": [],
            "pages": [],
            "search_evidence": [],
            "traversal_log": traversal,
            "error": root_msg
        }

# -------------------- API Validation --------------------

def validate_apis() -> Tuple[bool, str]:
    """
    Validate that both OpenAI and SerpAPI are working.
    
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        test_client = openai_client()
        
        test_resp = requests.get(SERP_API_URL, params={
            "engine": "google", "q": "test", "api_key": serp_key_required(), "num": 1
        }, timeout=10)
        
        if test_resp.status_code != 200:
            return False, "SerpAPI authentication failed"
        return True, ""
        
    except Exception as e:
        return False, f"API authentication failed: {e}" 