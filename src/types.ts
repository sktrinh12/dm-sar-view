export interface TableDataType {
  cellular_geomean: CellularGeomean[]
  compound_batch: CompoundBatch[]
  in_vivo_pk: InVivoPK[]
}

export interface BioTableDataType {
  biochemical_geomean: BiochemicalGeomean[]
}

interface BiochemicalGeomean {
  assay_type: string
  target: string
  variant: string | null
  cofactors: string
  geo_nm: number | null
  n_of_m: string
  created_date: string
}

interface CellularGeomean {
  assay_type: string
  cell: string
  variant: string
  geo_nm: number | null
  n_of_m: string
  created_date: string
}

interface CompoundBatch {
  BATCH_ID: string
  BATCH_REGISTERED_PROJECT: string
  registered_date: string
  SUPPLIER: string
  net_weight_mg: number
}

interface InVivoPK {
  species: string
  dose: number
  experiment_id: string
  administration: string
  auclast_d_result: number | null
  cl_obs_result: number
  cmax_result: number | null
  cmax_ratio_result: number | null
  KP_RESULT: number | null
  KP_UU_RESULT: number | null
  F_RESULT: number | null
  VSS_OBS_RESULT: number
  MRTINF_OBS_RESULT: number
  T1_2_RESULT: number
  created_date: string
}
