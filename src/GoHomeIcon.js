import IconButton from '@mui/material/IconButton'
import HomeIcon from '@mui/icons-material/Home'
import { Link } from 'react-router-dom'
import { colour } from './Colour.js'
import { createTheme, ThemeProvider } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    purpleColour: {
      main: colour,
    },
  },
})
const GoHomeIcon = () => {
  return (
    <ThemeProvider theme={theme}>
      <IconButton
        size='medium'
        component={Link}
        to='/'
        sx={{ color: 'purpleColour.main' }}
      >
        <HomeIcon />
      </IconButton>
    </ThemeProvider>
  )
}

export default GoHomeIcon
