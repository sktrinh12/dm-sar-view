import React, { useState, useEffect, ChangeEvent } from 'react'
import TextField from '@mui/material/TextField'
import DatePicker from 'react-datepicker'
import Button from '@mui/material/Button'
import { Grid, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import 'react-datepicker/dist/react-datepicker.css'
import { BACKEND_URL } from './BackendURL'

const Home: React.FC = () => {
  const [compoundIds, setCompoundIds] = useState<string[]>([])
  const currentDate = new Date()
  const sevenDaysAgo = new Date(currentDate.getTime() - 7 * 24 * 60 * 60 * 1000)

  const [dateStart, setDateStart] = useState<Date>(sevenDaysAgo)
  const [dateEnd, setDateEnd] = useState<Date>(currentDate)

  useEffect(() => {
    const fetchCmpIds = async () => {
      const urlParams = new URLSearchParams(window.location.search)
      const urlParamsObj = Object.fromEntries(urlParams)
      console.log(urlParams.toString())

      if (urlParamsObj.hasOwnProperty('dm_table')) {
        try {
          const url = `${BACKEND_URL}/v1/get_cmpid_from_tbl?${urlParams.toString()}`
          console.log(url)
          const response = await fetch(url)
          const data = await response.json()
          setCompoundIds(data)
        } catch (error) {
          console.error('Error fetching compound ids:', error)
        }
      }
    }
    fetchCmpIds()
  }, [])

  const navigate = useNavigate()

  const handleOnChangeDate = (dates: [Date, Date]) => {
    const [start, end] = dates
    setDateStart(start)
    setDateEnd(end)
  }

  const handleOnChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const inputText = event.target.value
    const items = inputText
      .split(/[\r\n\t]+/)
      .map((value) => value.trim())
      .filter((value) => value !== '')
    setCompoundIds(items)
  }

  const handleButtonClick = () => {
    const queryParams = new URLSearchParams()
    queryParams.append(
      'date_filter',
      `${dateStart
        .toLocaleDateString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
        })
        .replace(/\//g, '-')}_${dateEnd
        .toLocaleDateString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
        })
        .replace(/\//g, '-')}`
    )
    queryParams.append('compound_id', compoundIds.join('-'))
    console.log(`/sarView?${queryParams.toString()}`)
    navigate(`/sarView?${queryParams.toString()}`)
  }

  return (
    <Grid
      sx={{ flexGrow: 1, paddingTop: '15vh' }}
      justifyContent='center'
      container
      spacing={2}
    >
      <Grid item xs={12}>
        <Typography
          variant='h1'
          align='center'
          paddingBottom={5}
          style={{ color: '#343990ff' }}
        >
          SAR View
        </Typography>
      </Grid>
      <Grid item xs={2}>
        <Typography variant='h6' gutterBottom>
          Compound IDs
        </Typography>
        <TextField
          label='Compound IDs'
          placeholder='Paste compound Ids (separated by tabs or carriage returns)'
          onChange={handleOnChange}
          value={compoundIds.join('\n')}
          multiline
          maxRows={12}
        />
      </Grid>

      <Grid item xs={2}>
        <Typography variant='h6' gutterBottom>
          Date
        </Typography>

        <DatePicker
          selected={dateStart}
          showPreviousMonths
          onChange={handleOnChangeDate}
          showIcon
          startDate={dateStart}
          selectsRange
          endDate={dateEnd}
        />
      </Grid>
      <Grid item xs={2}>
        <Button variant='contained' onClick={handleButtonClick}>
          Submit
        </Button>
      </Grid>
    </Grid>
  )
}

export default Home
