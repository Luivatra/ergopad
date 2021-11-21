import { Typography, Box }  from '@mui/material';

const CenterTitle = ({ title, subtitle }) => {

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: '3rem' }}>
            <Box
                sx={{
                    textAlign: 'center'
                    , maxWidth: '768px'
                }}
            >
                <Typography variant='h2'>
                    {title}
                </Typography>

                <Typography
                    variant='subtitle1'
                >
                    {subtitle}
                </Typography>
            </Box>
        </Box>
    )
}

export default CenterTitle