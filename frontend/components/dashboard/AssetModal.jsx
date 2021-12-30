import { Typography, Modal, Box, Paper } from '@mui/material';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '50vw',
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  maxHeight: '80vh',
  overflowY: 'scroll',
};

const parseDescription = (description) => {
  try {
    return JSON.stringify(JSON.parse(description), null, 2);
  } catch (e) {
    try {
      return JSON.stringify(JSON.parse(description.slice(1)), null, 2);
    } catch (e) {
      return description;
    }
  }
};

const AssetModal = ({ open, handleClose, asset }) => {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.up('md'));

  return (
    <Modal
      keepMounted
      open={open}
      onClose={handleClose}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      <Box sx={matches ? style : { ...style, width: '85vw' }}>
        <Typography id="modal-modal-title" variant="h6" component="h2">
          {asset?.name}
        </Typography>
        <Typography
          id="modal-modal-description"
          sx={{ mt: 2, overflowX: 'scroll', fontSize: '0.8rem' }}
        >
          <pre>Description: {parseDescription(asset?.description)}</pre>
          <pre>id: {asset?.id}</pre>
          <pre>ch: {asset?.ch}</pre>
          <pre>token: {asset?.token}</pre>
          <pre>amount: {asset?.amount}</pre>
        </Typography>
        {asset?.r9 ? (
          <Paper variant="outlined" sx={{ mt: 5 }}>
            <img width="100%" src={asset?.r9} />
          </Paper>
        ) : null}
      </Box>
    </Modal>
  );
};

export default AssetModal;
