sql_columns = {
    "mol_structure": "MOLFILE",
    "biochemical_geomean": "ASSAY_TYPE, TARGET, VARIANT, COFACTORS, GEO_NM, N_OF_M, DATE_HIGHLIGHT",
    "cellular_geomean": "CELL, VARIANT, GEO_NM, ASSAY_TYPE, N_OF_M, DATE_HIGHLIGHT",
    "permeability": "A_B, B_A, EFFLUX_RATIO, CELL_TYPES, PCT_RECOVERY_AB, DATE_HIGHLIGHT",
    "protein_binding": "SPECIES, MATRIX, PCT_UNBOUND, DATE_HIGHLIGHT",
    "stability": "MATRIX, SPECIES, RESULT_TYPE_1, RESULT_1, DATE_HIGHLIGHT",
    "solubility": "CONDITION, RESULT, DATE_HIGHLIGHT",
    "metabolic_stability": "CYP, RESULT, COMMENTS, DATE_HIGHLIGHT",
    "pxr": "FOLD_INDUCTION, UNIT, CONC, DATE_HIGHLIGHT",
    "in_vivo_pk": "SPECIES, ADMINISTRATION, DOSE, AUCLAST_D_RESULT, CMAX_RESULT, CL_OBS_RESULT, VSS_OBS_RESULT, MRTINF_OBS_RESULT, T1_2_RESULT, F_RESULT, CMAX_RATIO_RESULT, KP_RESULT, KP_UU_RESULT, DATE_HIGHLIGHT",
    "compound_batch": "net_weight_mg, DATE_HIGHLIGHT",
}

dm_table_cols = """
SELECT column_name
FROM (
    SELECT column_name
    FROM user_tab_columns
    WHERE table_name = '{0}'
)
OFFSET 1 ROWS FETCH NEXT 1 ROWS ONLY
"""


sql_stmts = {
    "mol_structure": "SELECT {0} FROM C$PINPOINT.REG_DATA WHERE FORMATTED_ID = '{1}'",
    "biochemical_geomean": "select {0} from su_biochem_drc_stats where compound_id = '{1}' ORDER BY CREATED_DATE DESC",
    "cellular_geomean": """SELECT {0} FROM SU_CELLULAR_DRC_STATS WHERE COMPOUND_ID = '{1}' ORDER BY CREATED_DATE DESC""",
    "permeability": """SELECT {0} FROM FT_PERMEABILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "metabolic_stability": """SELECT {0} FROM FT_CYP_INHIBITION_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "protein_binding": """SELECT {0} FROM FT_PPB_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "stability": """SELECT {0} FROM METABOLIC_STABILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "solubility": """SELECT {0} FROM FT_SOLUBILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "pxr": """SELECT {0} FROM FT_PXR_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "in_vivo_pk": """SELECT {0} FROM FT_DMPK_IN_VIVO_PIVOT_VW WHERE COMPOUND_ID = '{1}' ORDER BY created_date DESC""",
    "compound_batch": """SELECT {0} FROM COMPOUND_BATCH WHERE compound_id = '{1}' ORDER BY registered_date DESC""",
}
