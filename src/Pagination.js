import React from 'react'
import ArrowCircleLeftIcon from '@mui/icons-material/ArrowCircleLeft'
import ArrowCircleRightIcon from '@mui/icons-material/ArrowCircleRight'
import IconButton from '@mui/material/IconButton'
import Chip from '@mui/material/Chip'
import { colour } from './Colour'

const Pagination = ({
  handlePreviousPage,
  handleNextPage,
  page,
  disableNext,
  totalCount,
  compoundsPerPage,
  disablePagination,
}) => {
  return (
    <>
      <IconButton
        aria-label='Previous'
        onClick={handlePreviousPage}
        disabled={disablePagination || page === 1}
      >
        <ArrowCircleLeftIcon />
      </IconButton>

      <Chip
        label={page}
        style={{ borderColor: colour, color: colour }}
        variant='outlined'
      />
      <IconButton
        aria-label='Next'
        onClick={handleNextPage}
        disabled={disablePagination || disableNext}
      >
        <ArrowCircleRightIcon />
      </IconButton>
      <Chip
        label={`${Math.ceil(
          totalCount / compoundsPerPage
        )} pages / total compounds: ${totalCount}`}
        style={{ color: colour }}
      />
    </>
  )
}

export default Pagination
