import IconButton from '@mui/material/IconButton'
import HomeIcon from '@mui/icons-material/Home'
import { Link, useNavigate } from 'react-router-dom'
import { colour } from './Colour.js'
import { createTheme, ThemeProvider } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    purpleColour: {
      main: colour,
    },
  },
})
const GoHomeIcon = ({ handleBeforeUnload }) => {
  const navigate = useNavigate()

  const handleClick = () => {
    handleBeforeUnload()
    navigate('/')
  }
  return (
    <ThemeProvider theme={theme}>
      <IconButton
        size='medium'
        component={Link}
        to='/'
        onClick={handleClick}
        sx={{ color: 'purpleColour.main' }}
      >
        <HomeIcon />
      </IconButton>
    </ThemeProvider>
  )
}

export default GoHomeIcon
