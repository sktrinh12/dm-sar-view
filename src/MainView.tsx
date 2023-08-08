import React, { useState, useEffect } from 'react'
import ReactLoading from 'react-loading'
import { colour } from './Colour'
import { TableDataType, BioTableDataType } from './types'
import TableGrid from './TableGrid.tsx'
import { AxiosResponse } from 'axios'
import axios from 'axios'
import Box from '@mui/material/Box'
import GoHomeIcon from './GoHomeIcon'
import Pagination from './Pagination'
import { BACKEND_URL } from './BackendURL'
import { compoundIdSort } from './sort'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
// import FetchContext, { FetchContextType } from './FetchedContext.tsx'

const height = 667
const width = 375

const axiosConfig = {
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
  },
}

const MainView: React.FC = () => {
  const compoundsPerPage = 12
  const [tableData, setTableData] = useState<TableDataType>({
    cellular_geomean: [],
    compound_batch: [],
    in_vivo_pk: [],
  })

  const [page, setPage] = useState<number>(1)
  const [user, setUser] = useState<string>('')
  const [triggeredMultiples, setTriggeredMultiples] = useState<Set<number>>(
    new Set()
  )

  const handleNextPage = () => {
    const currPage = page + 1
    setPage(currPage)
    // sessionStorage.setItem('page', currPage.toString())
    if (
      currPage % compoundsPerPage === 0 &&
      !triggeredMultiples.has(currPage)
    ) {
      triggerNextBatch()
      setTriggeredMultiples(new Set(triggeredMultiples).add(currPage))
    }
  }

  const handlePreviousPage = () => {
    // const currPage = page - 1
    setPage(page - 1)
    // sessionStorage.setItem('page', currPage.toString())
  }

  const triggerNextBatch = async () => {
    try {
      const nextBatchUrl = `${BACKEND_URL}/v1/next_batch?user=${user}&pages=${compoundsPerPage}`
      const response = await axios.get(nextBatchUrl, axiosConfig)
      console.log('Next batch triggered successfully')
      console.log('Request IDs:', response.data.request_ids)
    } catch (error) {
      console.log('Error triggering next batch:', error)
    }
  }

  const [requestIds, setRequestIds] = useState<string[]>([])
  const [compoundIds, setCompoundIds] = useState<string[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [bioLoading, setBioLoading] = useState<boolean>(true)
  const [bioTimer, setBioTimer] = useState<NodeJS.Timeout | undefined>()
  const [disablePagination, setDisablePagination] = useState<boolean>(true)
  const [fetched, setFetched] = useState<boolean>(false)
  // const { fetched, setFetched } = useContext(FetchContext) as FetchContextType

  const handleBeforeUnload = async () => {
    await axios.post(
      `${BACKEND_URL}/v1/cancel_batches?user=${user}`,
      axiosConfig
    )
    console.log(`canceled batch of ${user}`)
    if (bioTimer) {
      clearTimeout(bioTimer)
    }
    sessionStorage.removeItem('requestIds')
  }

  const fetchData = async (url: string, compoundIdsArray: Array<string>) => {
    setLoading(true)
    try {
      let response: AxiosResponse<any>

      if (compoundIdsArray.length === 0) {
        response = await axios.get(url, axiosConfig)
      } else {
        response = await axios.post(
          url,
          { compound_ids: compoundIdsArray },
          axiosConfig
        )
      }
      const json = response.data
      if (
        typeof BACKEND_URL !== 'undefined' &&
        BACKEND_URL.match(/localhost/g)
      ) {
        console.log(json)
      }
      if (response.status === 200) {
        if (compoundIdsArray.length > 0) {
          setRequestIds(json.request_ids)
          console.log(json.request_ids)
          sessionStorage.setItem('requestIds', JSON.stringify(json.request_ids))
          // sessionStorage.setItem('page', page.toString())
          // sessionStorage.setItem(
          // 'disablePagination',
          // disablePagination.toString()
          // )
          // sessionStorage.setItem(
          // 'compoundIds',
          // JSON.stringify(compoundIdsArray)
          // )
        }
        setTableData(json.data)
        setLoading(false)
      }
    } catch (err) {
      console.log('AXIOS ERROR: ', err)
      toast.error(
        'Failed to fetch data. Please wait a few more seconds and try again using the previous/next arrows within the app and not the browser',
        {
          position: 'top-center',
          autoClose: 3000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: false,
          progress: undefined,
          theme: 'light',
        }
      )
      setLoading(false)
    }
  }

  const fetchDataSlow = async (
    url: string,
    compoundIdsArray: Array<string>
  ) => {
    setBioLoading(true)
    try {
      let response: AxiosResponse<any>

      response = await axios.post(
        url,
        { compound_ids: compoundIdsArray },
        axiosConfig
      )
      if (response.status === 200) {
        const newData = response.data as Record<
          string,
          {
            row: Array<{ row: number }>
            compound_id: Array<{ FT_NUM: string }>
            biochemical_geomean: BioTableDataType['biochemical_geomean']
          }
        >
        // console.log(newData)

        setTableData((prevTableData) => {
          const updatedData = { ...prevTableData }

          Object.entries(newData.data).forEach(([cmpdId, data]) => {
            // console.log(data.biochemical_geomean)

            if (updatedData[cmpdId]) {
              updatedData[cmpdId].biochemical_geomean = data.biochemical_geomean
            }
          })

          const storedRequestIds = JSON.parse(
            sessionStorage.getItem('requestIds')
          )
          const firstRequestId =
            storedRequestIds && storedRequestIds.length > 0
              ? storedRequestIds[0]
              : null

          console.log(`firstRequestId: ${firstRequestId}`)

          // console.log(updatedData)
          updateBioData(firstRequestId, updatedData)

          return updatedData
        })
        setBioLoading(false)
        setLoading(false)
        if (bioTimer) {
          clearTimeout(bioTimer)
        }
        const timer = setTimeout(() => {
          setDisablePagination(false)
        }, 8200)
        setBioTimer(timer)
      }
    } catch (err) {
      console.log('AXIOS ERROR (fetchDataSlow) : ', err)
      toast.error(`Failed to fetch data - ${err}`, {
        position: 'top-center',
        autoClose: 3000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: false,
        progress: undefined,
        theme: 'light',
      })
      setBioLoading(false)
    }
  }

  const updateBioData = async (requestId: string, updatedData: any) => {
    try {
      const postResponse = await axios.post(
        `${BACKEND_URL}/v1/sar_view_sql_update_biochem?request_id=${requestId}`,
        { updatedData },
        axiosConfig
      )
      // console.log(postResponse)
      console.log(
        `updated data for ${requestId}, status: ${postResponse.status}`
      )
    } catch (err) {
      console.error('AXIOS ERROR during biochem update POST request: ', err)
    }
  }

  useEffect(() => {
    const fetchInitialData = async () => {
      const urlParams = new URLSearchParams(window.location.search)
      const urlParamsObj = Object.fromEntries(urlParams)
      console.log(urlParams.toString())
      setFetched(true)
      if (
        !urlParamsObj.hasOwnProperty('date_filter') ||
        !urlParamsObj.hasOwnProperty('session_id') ||
        !urlParamsObj.hasOwnProperty('user')
      ) {
        console.error('Error: Date, session ID, and user are required!')
      }
      let dateFilter: string = urlParamsObj.date_filter
      const sessionIdParam: string =
        urlParamsObj.session_id || 'ebc7e7a0-6b88-42e6-a7e9-placeholder'
      const userParam: string = urlParamsObj.user
      const userId: string = `${userParam}-${sessionIdParam}`
      setUser(userId)

      const compoundIdsString = sessionStorage.getItem(sessionIdParam)
      const compoundIdsArray = compoundIdsString
        ? compoundIdsString.split('-')
        : []
      compoundIdSort(compoundIdsArray)
      // console.log(compoundIdsArray)
      setCompoundIds(compoundIdsArray)
      let initialUrl = `${BACKEND_URL}/v1/sar_view_sql_set?date_filter=${dateFilter}&user=${userId}&pages=${compoundsPerPage}&fast_type=0`
      console.log(initialUrl)
      await fetchData(initialUrl, compoundIdsArray)
      const slowUrl = initialUrl.replace('fast_type=0', 'fast_type=-1')
      // console.log(slowUrl)
      const compoundIdsArrayForBio = compoundIdsArray.slice(0, compoundsPerPage)
      // console.log(compoundIdsArrayForBio)
      await fetchDataSlow(slowUrl, compoundIdsArrayForBio)
    }

    const fetchPaginatedData = async () => {
      // const savedRequestIds = sessionStorage.getItem('requestIds')
      // console.log(savedRequestIds)
      // const parsedRequestIds = JSON.parse(savedRequestIds)
      // console.log(page)
      // console.log(parsedRequestIds[page - 1])
      const paginatedUrl = `${BACKEND_URL}/v1/sar_view_sql_get?request_id=${
        requestIds[page - 1]
        // parsedRequestIds[page - 1]
      }`
      console.log(paginatedUrl)
      await fetchData(paginatedUrl, [])
      setBioLoading(false)
    }

    // console.log(`fetch: ${fetched}`)

    if (!fetched) {
      fetchInitialData()
    } else {
      // const savedPage = sessionStorage.getItem('page')
      // const savedDisablePagination = sessionStorage.getItem('disablePagination')
      // const savedCompoundIds = sessionStorage.getItem('compoundIds')
      // const parsedPage = savedPage ? parseInt(savedPage, 10) : 1
      // const parsedDisablePagination = savedDisablePagination === 'true'
      // const parsedCompoundIds = savedCompoundIds
      //   ? JSON.parse(savedCompoundIds)
      //   : []
      // setPage(parsedPage)
      // setDisablePagination(parsedDisablePagination)
      // setCompoundIds(parsedCompoundIds)
      fetchPaginatedData()
    }

    return () => {
      if (bioTimer) {
        clearTimeout(bioTimer)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            <GoHomeIcon handleBeforeUnload={handleBeforeUnload} />
            <Pagination
              handleNextPage={handleNextPage}
              handlePreviousPage={handlePreviousPage}
              page={page}
              disableNext={page * compoundsPerPage >= compoundIds.length}
              totalCount={compoundIds.length}
              compoundsPerPage={compoundsPerPage}
              disablePagination={disablePagination}
            />
          </Box>
          <TableGrid tableData={tableData} bioLoading={bioLoading} />

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
              disablePagination={disablePagination}
            />
          </Box>
        </>
      )}
      <ToastContainer />
    </>
  )
}

export default MainView
