"""
Parser to extract structured data from AMED project pages
"""
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Keywords to identify column roles from header text
_TITLE_KEYWORDS = ['課題名', '課題', '補助事業課題名']
_RESEARCHER_KEYWORDS = ['代表者', '氏名', '研究者', 'First Name', 'Last Name']
_INSTITUTION_KEYWORDS = ['所属', '機関', '大学', '代表機関', '実施機関']
_POSITION_KEYWORDS = ['役職', '職名', '職位']
_SKIP_KEYWORDS = ['公募', '分野', '開発フェーズ', 'お問い合わせ', '申請', '採択', '応募',
                   '書面', 'ヒアリング', '課題番号', '海外研究拠点',
                   'AMED-CREST', 'PRIME']

# Common position values (used for heuristic detection)
_POSITION_VALUES = {
    '教授', '准教授', '助教', '講師', '特任教授', '特任准教授', '客員教授',
    '部長', '副部長', '室長', '課長', '医長', '医員',
    'センター長', '副センター長', '所長', '副所長', '院長', '副院長',
    '主任研究員', '研究員', '主幹研究員', '上席研究員', '特任研究員',
    'グループリーダー', 'チームリーダー', 'ユニットリーダー',
    '理事', '理事長', '主任', 'ディレクター', 'Director',
    'Professor', 'Associate Professor', 'Assistant Professor', 'Researcher',
    'Senior Researcher', 'Research Fellow', 'Postdoctoral Fellow',
    'Assistant Member', 'Associate Member', 'Member',
}


def _classify_header(header_text):
    """Classify a header column as title/researcher/institution/position/skip/unknown."""
    h = header_text.strip()
    if any(kw in h for kw in _SKIP_KEYWORDS):
        return 'skip'
    if any(kw in h for kw in _TITLE_KEYWORDS):
        return 'title'
    # Check institution before researcher since '代表機関' contains '代表'
    if any(kw in h for kw in _INSTITUTION_KEYWORDS):
        return 'institution'
    if any(kw in h for kw in _RESEARCHER_KEYWORDS):
        return 'researcher'
    if h in ('国', '相手国'):
        return 'skip'
    if any(kw in h for kw in _POSITION_KEYWORDS):
        return 'position'
    if h in ('#', '', '分類', '国', '公募枠', '番号'):
        return 'skip'
    return 'unknown'


def _detect_column_mapping(table):
    """Detect column roles from table headers. Returns a dict mapping role -> column index.

    Tries all header rows and picks the best one (most recognized roles with a title column).
    For multi-header tables (e.g. ASPIRE), merges mappings from multiple header rows.
    """
    best_mapping = None
    best_header_len = 0

    for row in table.find_all('tr'):
        ths = row.find_all('th')
        if not ths:
            continue
        headers = [th.get_text(strip=True) for th in ths]
        roles = [_classify_header(h) for h in headers]
        if 'title' not in roles:
            continue
        mapping = {}
        for i, role in enumerate(roles):
            if role not in ('skip', 'unknown') and role not in mapping:
                mapping[role] = i
        if 'title' in mapping:
            # Prefer mappings with more recognized roles
            if best_mapping is None or len(mapping) > len(best_mapping):
                best_mapping = mapping
                best_header_len = len(headers)

    if best_mapping:
        return best_mapping, best_header_len
    return None, 0


def _is_position_value(text):
    """Check if text looks like a position/title rather than an institution."""
    t = text.strip()
    if t in _POSITION_VALUES:
        return True
    # Partial matches for compound positions like "特任教授", "名誉教授" etc.
    if re.match(r'^(名誉|特任|客員|特命|寄附講座)?(教授|准教授|助教|講師)$', t):
        return True
    if re.match(r'^(副)?(部長|室長|課長|所長|院長|センター長|理事長?)$', t):
        return True
    # English positions (possibly with parenthetical details)
    if re.match(r'^(Full |Senior |Associate |Assistant )?(Professor|Researcher|Fellow|Member|Director)', t):
        return True
    return False


def _is_institution_value(text):
    """Check if text looks like an institution name."""
    t = text.strip()
    inst_patterns = ['大学', '研究所', '研究センター', '病院', '機構',
                     'センター', '学校', '学院', 'University', 'Institute',
                     'Hospital', '株式会社', '法人']
    return any(p in t for p in inst_patterns)


def _has_headers(table):
    """Check if a table has any header rows."""
    for row in table.find_all('tr'):
        ths = row.find_all('th')
        if ths and len(ths) >= 2:
            return True
    return False


def _extract_projects_from_table(table):
    """Extract projects from a single table, using header-based column detection."""
    mapping, header_len = _detect_column_mapping(table)

    # If table has headers but we couldn't find a title column,
    # it's likely not a project table (e.g., researcher list, statistics)
    if not mapping and _has_headers(table):
        return []

    projects = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) < 2:
            continue

        if mapping:
            # Header-based extraction
            title_idx = mapping.get('title')
            researcher_idx = mapping.get('researcher')
            institution_idx = mapping.get('institution')
            position_idx = mapping.get('position')

            if title_idx is None or title_idx >= len(cols):
                continue

            title = cols[title_idx].get_text(strip=True) if title_idx < len(cols) else ''
            researcher = cols[researcher_idx].get_text(strip=True) if researcher_idx is not None and researcher_idx < len(cols) else ''
            institution = cols[institution_idx].get_text(strip=True) if institution_idx is not None and institution_idx < len(cols) else ''
            position = cols[position_idx].get_text(strip=True) if position_idx is not None and position_idx < len(cols) else ''

        elif len(cols) >= 4:  # noqa: SIM114
            # Fallback: positional extraction for tables without recognizable headers
            title = cols[-4].get_text(strip=True)
            researcher = cols[-3].get_text(strip=True)
            institution = cols[-2].get_text(strip=True)
            position = cols[-1].get_text(strip=True)
        else:
            continue

        # Skip header-like rows
        skip_values = {'研究代表者', '研究開発代表者名', '所属機関', '研究開発代表者',
                       '所属', '役職', '役職名', '研究開発課題名', '課題名', '職名',
                       '補助事業課題名', '実施機関', '認定ベンチャーキャピタル'}
        if researcher in skip_values or title in skip_values:
            continue
        if institution in skip_values:
            continue
        if not title:
            continue

        # Skip rows that are clearly not project data
        # (numeric-only values indicate summary/statistics tables)
        if title.isdigit() or (researcher and researcher.isdigit()):
            continue
        # Skip if title is too short (likely a category label, not a project title)
        if len(title) < 5 and not any('\u4e00' <= c <= '\u9fff' for c in title):
            continue
        # Skip position-only researcher values
        if _is_position_value(researcher):
            continue

        # Heuristic fix: if institution looks like a position and position looks
        # like an institution, swap them
        if _is_position_value(institution) and _is_institution_value(position):
            institution, position = position, institution

        # Heuristic fix: if researcher looks like an institution and institution
        # looks like a person name, swap them
        if _is_institution_value(researcher) and not _is_institution_value(institution):
            researcher, institution = institution, researcher

        # If institution is still a position value, it's likely a 3-field row
        # where institution is missing — move it to position
        if _is_position_value(institution) and not position:
            position = institution
            institution = ''

        projects.append({
            'title': title,
            'researcher': researcher,
            'institution': institution,
            'position': position,
        })

    return projects


def parse_project_page(html, url):
    """Parse a project page and extract structured data"""
    soup = BeautifulSoup(html, 'lxml')

    # Extract title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else None

    # Extract date from title or page
    date_match = re.search(r'(令和|平成)(\d+)年(\d+)月(\d+)日', html)
    date_str = None
    if date_match:
        era, year, month, day = date_match.groups()
        # Convert Japanese era to Western year
        year_offset = 2018 if era == '令和' else 1988
        western_year = int(year) + year_offset
        date_str = f"{western_year}-{month.zfill(2)}-{day.zfill(2)}"

    # Extract program name from title
    program_name = None
    if title:
        match = re.search(r'「(.+?)」', title)
        if match:
            program_name = match.group(1)

    # Extract project tables
    projects = []
    tables = soup.find_all('table')

    for table in tables:
        projects.extend(_extract_projects_from_table(table))

    # Check for young researcher flag
    young_researcher = '若手あり' in html or '若手' in html

    return {
        'url': url,
        'page_title': title,
        'program_name': program_name,
        'date': date_str,
        'young_researcher_flag': young_researcher,
        'projects': projects
    }

if __name__ == '__main__':
    import json
    from pathlib import Path
    
    # Load sample projects
    data_dir = Path(__file__).parent.parent / 'data'
    with open(data_dir / 'sample_projects.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    # Parse each sample
    parsed = []
    for sample in samples:
        result = parse_project_page(sample['html'], sample['url'])
        parsed.append(result)
        print(f"\nParsed: {result['page_title']}")
        print(f"  Program: {result['program_name']}")
        print(f"  Date: {result['date']}")
        print(f"  Projects: {len(result['projects'])}")
    
    # Save parsed data
    with open(data_dir / 'parsed_samples.json', 'w', encoding='utf-8') as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved parsed data to data/parsed_samples.json")
