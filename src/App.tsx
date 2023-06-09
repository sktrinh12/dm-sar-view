import React, { useState, useEffect, ChangeEvent, ClipboardEvent } from 'react'
import { styled } from '@mui/system'
import TextareaAutosize from '@mui/base/TextareaAutosize'
import DatePicker from 'react-datepicker'
import Button from '@mui/material/Button'
import { Grid, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import 'react-datepicker/dist/react-datepicker.css'
import { BACKEND_URL } from './BackendURL'

const blue = {
  100: '#DAECFF',
  200: '#b6daff',
  400: '#3399FF',
  500: '#007FFF',
  600: '#0072E5',
  900: '#003A75',
}

const grey = {
  50: '#f6f8fa',
  100: '#eaeef2',
  200: '#d0d7de',
  300: '#afb8c1',
  400: '#8c959f',
  500: '#6e7781',
  600: '#57606a',
  700: '#424a53',
  800: '#32383f',
  900: '#24292f',
}

const StyledTextarea = styled(TextareaAutosize)(
  ({ theme }) => `
    width: 320px;
    font-family: IBM Plex Sans, sans-serif;
    font-size: 0.875rem;
    font-weight: 400;
    line-height: 1.5;
    padding: 12px;
    border-radius: 12px 12px 0 12px;
    color: ${theme.palette.mode === 'dark' ? grey[300] : grey[900]};
    background: ${theme.palette.mode === 'dark' ? grey[900] : '#fff'};
    border: 1px solid ${theme.palette.mode === 'dark' ? grey[700] : grey[200]};
    box-shadow: 0px 2px 24px ${
      theme.palette.mode === 'dark' ? blue[900] : blue[100]
    };

    &:hover {
      border-color: ${blue[400]};
    }

    &:focus {
      border-color: ${blue[400]};
      box-shadow: 0 0 0 3px ${
        theme.palette.mode === 'dark' ? blue[600] : blue[200]
      };
    }

    // firefox
    &:focus-visible {
      outline: 0;
    }
  `
)

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

  const handleOnPaste = (event: ClipboardEvent<HTMLTextAreaElement>) => {
    const pastedText = event.clipboardData.getData('text/plain')
    const parsedValues = pastedText
      .split(/[\r\n\t]+/)
      .map((value) => value.trim())
      .filter((value) => value !== '')
    setCompoundIds(parsedValues)
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
      sx={{ flexGrow: 1, paddingTop: '25vh' }}
      justifyContent='center'
      container
      spacing={2}
    >
      <Grid item xs={3}>
        <Typography variant='h6' gutterBottom>
          Compound IDs
        </Typography>
        <StyledTextarea
          aria-label='Compound IDs text area'
          placeholder='Paste compound Ids (separated by tabs or carriage returns)'
          onChange={handleOnChange}
          onPaste={handleOnPaste}
          value={compoundIds.join('\n')}
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
