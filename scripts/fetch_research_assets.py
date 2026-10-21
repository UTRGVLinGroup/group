"""Download pinned, public research assets; run only when refreshing local assets."""
import json
from pathlib import Path
import urllib.request
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent

def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "FacultyWebsiteAssetPreparation/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()

license_url = "https://raw.githubusercontent.com/3dmol/3Dmol.js/2.0.4/LICENSE"
(ROOT / "assets/vendor/3Dmol-LICENSE.txt").write_bytes(download(license_url))
records = []
for name, expected in [
    ("chlorosulfonic acid", "ClHO3S"),
    ("3,4,5-trifluorobenzoic acid", "C7H3F3O2"),
    ("3,5-difluorobenzoic acid", "C7H4F2O2"),
    ("1,1-diiodoethane", "C2H4I2"),
    ("3,3,3-trifluoro-2-(trifluoromethyl)propanoic acid", "C4H2F6O2"),
    ("formic acid", "CH2O2"),
]:
    prefix = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}"
    properties = json.loads(download(prefix + "/property/MolecularFormula,IUPACName/JSON"))["PropertyTable"]["Properties"][0]
    assert properties["MolecularFormula"] == expected, f"Unexpected structure: {properties}"
    cid = properties["CID"]
    prefix = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}"
    time.sleep(0.3)
    sdf = download(prefix + "/SDF?record_type=3d")
    assert b"V2000" in sdf and b"M  END" in sdf, f"Invalid SDF: {cid}"
    (ROOT / f"assets/models/{cid}.sdf").write_bytes(sdf)
    records.append({"name": name, **properties, "source": prefix + "/SDF?record_type=3d"})
    print(properties)
    time.sleep(0.3)
(ROOT / "assets/models/sources.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
(ROOT / "backups/original-links.html").write_bytes(download("https://faculty.utrgv.edu/wei.lin/links.html"))
print("Research assets saved.")
