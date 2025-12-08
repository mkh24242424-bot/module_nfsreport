"""
Report type phraser mappings for NFSReportWriter.

Each report type defines phraser functions for different block types
across STR and YSTR kits.
"""

from typing import Dict, Callable
import module.NFS_REPORTPHRASER as NFS_RP

# Type alias for phraser mapping
PhraserMapping = Dict[str, Dict[str, Callable]]

REPORT_TYPE_PHRASERS: Dict[str, PhraserMapping] = {
    "default": {
        "STR": {
            "대조": NFS_RP.make_phrase_deceased,
            "대조일치": NFS_RP.make_phrase_ref,
            "대표일치": NFS_RP.make_phrase_res,
            "ND": NFS_RP.make_phrase_nd,
            "NC": NFS_RP.make_phrase_nc,
        },
        "YSTR": {
            "대조": NFS_RP.make_phrase_suspect_match_y,
            "대조일치": NFS_RP.make_phrase_ref_y,
            "대표일치": NFS_RP.make_phrase_res_y,
            "ND": NFS_RP.make_phrase_nd_y,
            "NC": NFS_RP.make_phrase_nc_y,
        }
    },
    # Future report types can be added here
    # "suspect": {...},
    # "paternity": {...},
}




# Valid report type names (for validation)
VALID_REPORT_TYPES = set(REPORT_TYPE_PHRASERS.keys())
