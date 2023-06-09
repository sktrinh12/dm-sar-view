import React, { useState, useEffect } from 'react'
import ReactLoading from 'react-loading'
import { colour } from './Colour'
import { TableDataType } from './types'
import TableGrid from './TableGrid.tsx'
import { AxiosResponse, AxiosError } from 'axios'
import axios from 'axios'
import Box from '@mui/material/Box'
import GoHomeIcon from './GoHomeIcon'
import Pagination from './Pagination'
import { BACKEND_URL } from './BackendURL'
import { compoundIdSort } from './sort'
// import { data } from './mockData.js'

const height = 667
const width = 375

const axiosConfig = {
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
  },
}

const MainView: React.FC = () => {
  const [tableData, setTableData] = useState<TableDataType>({
    biochemical_geomean: [],
    cellular_geomean: [],
    compound_batch: [],
    in_vivo_pk: [],
  })

  const [page, setPage] = useState(1)

  const handleNextPage = () => {
    setPage(page + 1)
  }

  const handlePreviousPage = () => {
    setPage(page - 1)
  }
  const [compoundIds, setCompoundIds] = useState<string[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const compoundsPerPage = 10

  const fetchData = async (url: string) => {
    setLoading(true)
    await axios
      .get(url, axiosConfig)
      .then(async (res: AxiosResponse<any>) => {
        const json = res.data
        if (
          typeof BACKEND_URL !== 'undefined' &&
          BACKEND_URL.match(/localhost/g)
        ) {
          console.log(json)
        }
        if (res.status === 200) {
          setTableData(json)
          setLoading(false)
        }
      })
      .catch((err: AxiosError<any>) => {
        console.log('AXIOS ERROR: ', err)
      })
    // setLoading(false)
    // setTableData(data)
  }

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const urlParamsObj = Object.fromEntries(urlParams)
    let hyphenCurrentCompoundId: string
    console.log(urlParams.toString())

    if (
      !urlParamsObj.hasOwnProperty('date_filter') ||
      !urlParamsObj.hasOwnProperty('compound_id')
    ) {
      console.error('Error: Date or compound ID is missing!')
    }
    const dateFilter = urlParamsObj.date_filter
    const compoundIdParam = urlParamsObj.compound_id
    const compoundIdsArray = compoundIdParam.split('-')
    compoundIdSort(compoundIdsArray)
    console.log(compoundIdsArray)
    const start = (page - 1) * compoundsPerPage
    const end = start + compoundsPerPage
    setCompoundIds(compoundIdsArray)
    if (compoundIdsArray.length > compoundsPerPage) {
      const subsetCompoundIds = compoundIdsArray.slice(start, end)
      hyphenCurrentCompoundId = subsetCompoundIds.join('-')
    } else {
      hyphenCurrentCompoundId = compoundIdParam
    }

    const url = `${BACKEND_URL}/v1/sar_view_sql?sql_type=blank&type=blank&date_filter=${dateFilter}&compound_id=${hyphenCurrentCompoundId}`
    console.log(url)
    fetchData(url)
    return () => {}
  }, [page])

  return (
    <>
      {loading ? (
        <div
          style={{
            margin: 'auto',
            padding: '10px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <ReactLoading
            type='spin'
            color={colour}
            height={height}
            width={width}
          />
        </div>
      ) : (
        <>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'center',
              p: 1,
            }}
          >
            <GoHomeIcon />
            <Pagination
              handleNextPage={handleNextPage}
              handlePreviousPage={handlePreviousPage}
              page={page}
              disableNext={page * compoundsPerPage >= compoundIds.length}
              totalCount={compoundIds.length}
              compoundsPerPage={compoundsPerPage}
            />
          </Box>
          <TableGrid tableData={tableData} />

          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'center',
              p: 1,
            }}
          >
            <Pagination
              handleNextPage={handleNextPage}
              handlePreviousPage={handlePreviousPage}
              page={page}
              disableNext={page * compoundsPerPage >= compoundIds.length}
              totalCount={compoundIds.length}
              compoundsPerPage={compoundsPerPage}
            />
          </Box>
        </>
      )}
    </>
  )
}

export default MainView
