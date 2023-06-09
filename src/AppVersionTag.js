import React from 'react'
import { Box } from '@mui/system'
import { useTheme } from '@mui/material/styles'
import Typography from '@mui/material/Typography'

const AppVersion = () => {
  const theme = useTheme()
  const version = process.env.REACT_APP_VERSION
  const env = process.env.REACT_APP_ENVIRONMENT

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: theme.spacing(1),
        right: theme.spacing(1),
        backgroundColor: '#f2f2f2',
        color: '#858585',
        padding: theme.spacing(0.5),
        borderRadius: '4px',
      }}
    >
      <Typography variant='caption' component='span'>
        {`${env}_v${version}`}
      </Typography>
    </Box>
  )
}

export default AppVersion
