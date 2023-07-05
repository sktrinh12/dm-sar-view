sql_columns = {
    "mol_structure": "MOLFILE",
    "biochemical_geomean": "ASSAY_TYPE, TARGET, VARIANT, COFACTORS, GEO_NM, N_OF_M, DATE_HIGHLIGHT",
    "cellular_geomean": "ASSAY_TYPE, CELL, VARIANT, GEO_NM, N_OF_M, DATE_HIGHLIGHT",
    "in_vivo_pk": "SPECIES, DOSE, EXPERIMENT_ID, ADMINISTRATION, AUCLAST_D_RESULT, CL_OBS_RESULT, CMAX_RESULT, CMAX_RATIO_RESULT, KP_RESULT, KP_UU_RESULT, F_RESULT, VSS_OBS_RESULT, MRTINF_OBS_RESULT, T1_2_RESULT, DATE_HIGHLIGHT",
    "compound_batch": "BATCH_ID, BATCH_REGISTERED_PROJECT, net_weight_mg, SUPPLIER, DATE_HIGHLIGHT",
    "metabolic_stability": "CYP, RESULT, COMMENTS, DATE_HIGHLIGHT",
    "pxr": "FOLD_INDUCTION, UNIT, CONC, DATE_HIGHLIGHT",
    "permeability": "BATCH_ID, A_B, B_A, EFFLUX_RATIO, CELL_TYPES, PCT_RECOVERY_AB, DATE_HIGHLIGHT",
    "protein_binding": "SPECIES, MATRIX, PCT_UNBOUND, DATE_HIGHLIGHT",
    "solubility": "CONDITION, RESULT, DATE_HIGHLIGHT",
    "stability": "MATRIX, SPECIES, RESULT_TYPE_1, RESULT_1, DATE_HIGHLIGHT",
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

sar_biochem_sql_dict = {
    "select": """
    MAX(t0.ASSAY_TYPE) AS assay_type,
    MAX(t0.TARGET) AS target,
    MAX(t0.VARIANT) AS variant,
    MAX(t0.COFACTORS) AS cofactors,
    MAX(t0.GEOMEAN_NM) AS geo_nM,
    max(t0.n) || ' of ' || max(t0.m) AS n_of_m,
    TO_CHAR(max(t0.created_date)) as created_date,
    max(t0.date_highlight) as date_highlight
""",
    "inner_select": """
    CRO,
    ASSAY_TYPE,
    COMPOUND_ID,
    BATCH_ID,
    TARGET,
    VARIANT,
    COFACTORS,
    ATP_CONC_UM,
    MODIFIER,
    CREATED_DATE,
    DATE_HIGHLIGHT,
""",
    "geomean": """
    ROUND(POWER(10, AVG(LOG(10, ic50)) OVER(PARTITION BY
      CRO,
      ASSAY_TYPE,
      COMPOUND_ID,
      TARGET,
      VARIANT,
      COFACTORS,
      ATP_CONC_UM,
      MODIFIER
)) * TO_NUMBER('1.0e+09'), 1) AS geomean_nM,
""",
    "count": """
    count(t1.ic50) OVER(PARTITION BY t1.compound_id,
        t1.cro,
        t1.assay_type,
        t1.target,
        t1.variant,
        t1.cofactors,
        t1.atp_conc_um,
        t1.modifier) AS n,
    count(t1.ic50) OVER(PARTITION BY t1.compound_id,
        t1.cro,
        t1.assay_type,
        t1.target,
        t1.variant,
        t1.cofactors,
        t1.atp_conc_um) AS m
""",
    "group_by": """
    t0.COMPOUND_ID,
    t0.CRO,
    t0.ASSAY_TYPE,
    t0.TARGET,
    t0.VARIANT,
    t0.COFACTORS,
    t0.ATP_CONC_UM
""",
}

sql_stmts = {
    "mol_structure": "SELECT {0} FROM C$PINPOINT.REG_DATA WHERE FORMATTED_ID = '{1}'",
    "biochemical_geomean": f"""SELECT {sar_biochem_sql_dict['select']}
    FROM ( SELECT {sar_biochem_sql_dict['inner_select']} {sar_biochem_sql_dict['geomean']} {sar_biochem_sql_dict['count']}
    FROM DS3_USERDATA.SU_BIOCHEM_DRC t1
    WHERE
        ASSAY_INTENT = 'Screening'
        AND VALIDATED = 'VALIDATED'
    ) t0 WHERE t0.MODIFIER IS NULL and t0.COMPOUND_ID = '{{1}}'
    GROUP BY {sar_biochem_sql_dict['group_by']}
    ORDER BY CREATED_DATE DESC
    """,
    "cellular_geomean": """SELECT {0} FROM SU_CELLULAR_DRC_STATS WHERE COMPOUND_ID = '{1}' ORDER BY CREATED_DATE DESC""",
    "in_vivo_pk": """SELECT {0} FROM FT_DMPK_IN_VIVO_PIVOT_VW WHERE COMPOUND_ID = '{1}' ORDER BY created_date DESC""",
    "compound_batch": """SELECT {0} FROM COMPOUND_BATCH WHERE compound_id = '{1}' ORDER BY registered_date DESC""",
    "metabolic_stability": """SELECT {0} FROM FT_CYP_INHIBITION_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "pxr": """SELECT {0} FROM FT_PXR_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "permeability": """SELECT {0} FROM FT_PERMEABILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "protein_binding": """SELECT {0} FROM FT_PPB_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "solubility": """SELECT {0} FROM FT_SOLUBILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
    "stability": """SELECT {0} FROM METABOLIC_STABILITY_VW WHERE COMPOUND_ID = '{1}' ORDER BY EXPERIMENT_DATE DESC""",
}
