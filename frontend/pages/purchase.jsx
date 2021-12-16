import { Typography, Grid, Box, TextField, Button, Container } from '@mui/material';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import FilledInput from '@mui/material/FilledInput';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import FormHelperText from '@mui/material/FormHelperText';
import PageTitle from '@components/PageTitle';
import theme from '../styles/theme';
import axios from 'axios';
import { useWallet } from 'utils/WalletContext'
import { useAddWallet } from 'utils/AddWalletContext'
import { useState, useEffect, forwardRef } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import MuiNextLink from '@components/MuiNextLink'
import Image from 'next/image';

const Alert = forwardRef(function Alert(props, ref) {
	return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
  });

const initialFormData = Object.freeze({
    wallet: '',
    tokens: 0.0,
    sigusd: 0.0
  });

const initialFormErrors = Object.freeze({
    wallet: false,
    sigusd: false
});

const initialCheckboxState = Object.freeze({
    legal: false,
    risks: false,
    dao: false
})

const initialSuccessMessage = Object.freeze({
    ergs: '12',
    address: 'xyz'
})

const Purchase = () => {
    // boolean object for each checkbox
    const [checkboxState, setCheckboxState] = useState(initialCheckboxState)

    // set true to disable submit button
    const [buttonDisabled, setbuttonDisabled] = useState(true)

    // loading spinner for submit button
    const [isLoading, setLoading] = useState(false);

    // form error object, all booleans
    const [formErrors, setFormErrors] = useState(initialFormErrors)
    
    const [formData, updateFormData] = useState(initialFormData);

    // open error snackbar 
	const [openError, setOpenError] = useState(false);

    // open success modal
	const [openSuccess, setOpenSuccess] = useState(false);

    // change error message for error snackbar
	const [errorMessage, setErrorMessage] = useState('Please eliminate form errors and try again')

    const [successMessage, setSuccessMessage] = useState(initialSuccessMessage)


    const { wallet } = useWallet()
    const { setAddWalletOpen } = useAddWallet()

    const openWalletAdd = () => {
        setAddWalletOpen(true)
    }

    useEffect(() => {

        ////////////////////////////////////////////////////////////////////////////
        //////////// REQUIRES API CALL TO CHECK ////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////
        const approvedWallet = '9gvdWNaoVqSGwedW77J7BJ3ghWY1UuqQpGw22JxwWqaNPSXLZnt'

        if (wallet == approvedWallet) {
            setFormErrors({
                ...formErrors,
                wallet: false
            });
            updateFormData({
                ...formData,
                wallet: wallet
            });
        }
        else {
            setFormErrors({
                ...formErrors,
                wallet: true
            });
        }
    }, [wallet])

    useEffect(() => {
        if (isLoading) {
            setbuttonDisabled(true)
        }
        else {
            setbuttonDisabled(false)
        }
    }, [isLoading])

    const handleChecked = (e) => {
        setCheckboxState({
            ...checkboxState,
            [e.target.name]: e.target.checked
        })
    }

    const { legal, risks, dao } = checkboxState;
    const checkboxError = [legal, risks, dao].filter((v) => v).length !== 3

    useEffect(() => {
        checkboxError ? setbuttonDisabled(true) : setbuttonDisabled(false)
    }, [checkboxError])

    // snackbar for error reporting
	const handleCloseError = (event, reason) => {
		if (reason === 'clickaway') {
			return;
		}
		setOpenError(false);
	};

    // modal for success message
	const handleCloseSuccess = () => {
		setOpenSuccess(false);
	};

    const handleChange = (e) => {
        if (e.target.value == '' || e.target.value == 0.0) {
			setFormErrors({
				...formErrors,
				[e.target.name]: true
			});
		}
		else {
			setFormErrors({
				...formErrors,
				[e.target.name]: false
			});
		}

        if (e.target.name == 'sigusd') {
            
            ////////////////////////////////////////////////////////////////////////////
            //////////// REQUIRES API CALL TO CHECK ////////////////////////////////////
            ////////////////////////////////////////////////////////////////////////////
            const maxSig = 3000.0

			const sigNumber = Number(e.target.value)
			if (sigNumber <= maxSig && sigNumber > 0.0 ) {
				setFormErrors({
					...formErrors,
					sigusd: false
				});
                updateFormData({
                    ...formData,
                    sigusd: sigNumber,
                    tokens: (sigNumber / 0.011)
                });
			}
			else {
				setFormErrors({
					...formErrors,
					sigusd: true
				});
			}
		}
        
        console.log(formErrors)
      };

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true)

		const emptyCheck = Object.values(formData).every(v => (v != '') || (v != 0))
		const errorCheck = Object.values(formErrors).every(v => v === false)

        console.log(formData)
        console.log(formErrors)

        console.log('empty: ' + emptyCheck + ' error: ' + errorCheck)
		
		if (errorCheck && emptyCheck) { 
            console.log(formData)
			axios.post(`${process.env.API_URL}/blockchain/purchase`, { ...formData })
            .then(res => {
                console.log(res);
                console.log(res.data);
                setLoading(false)

                // modal for success message
				setOpenSuccess(true)
            })
            .catch((err) => {
                // snackbar for error message
				setErrorMessage('ERROR POSTING: ' + err)
                setLoading(false)
            }); 
            setLoading(false)
            setOpenSuccess(true)
		}
		else {
			let updateErrors = {}
			Object.entries(formData).forEach(entry => {
				const [key, value] = entry;
				if (value == '') {
                    if (Object.hasOwn(formErrors, key)){
                        let newEntry = {[key]: true}
                        updateErrors = {...updateErrors, ...newEntry};
                    }
				}
			})

			setFormErrors({
				...formErrors,
				...updateErrors
			})

            // snackbar for error message
			setErrorMessage('Please eliminate form errors and try again')
			setOpenError(true)

            // turn off loading spinner for submit button
			setLoading(false)
		}
    };

  return (
    <>
        <Container maxWidth="lg" sx={{ px: {xs: 2, md: 3 } }}>
		<PageTitle 
			title="Purchase ErgoPad Tokens"
			subtitle="If you are approved for seed-sale whitelist, you can purchase tokens here."
		/>
        </Container>

        <Grid container maxWidth='lg' sx={{ mx: 'auto', flexDirection: 'row-reverse', px: {xs: 2, md: 3 } }}>

            <Grid item md={4} sx={{ pl: { md: 4, xs: 0 } }}>
				<Box sx={{ mt: { md: 0, xs: 4 } }}>
                    <Typography variant="h4" sx={{ fontWeight: '700', lineHeight: '1.2' }}>
                        Details
                    </Typography>
                
                    <Typography variant="p" sx={{ fontSize: '1rem', mb: 3 }}>
                        You must be pre-approved on whitelist to be able to purchase tokens. Add your wallet address to check if you have an allocation available. 
                    </Typography>
				</Box>
			</Grid>

			<Grid item md={8}>
				<Box component="form" noValidate onSubmit={handleSubmit}>
					<Typography variant="h4" sx={{ mb: 3, fontWeight: '700' }}>
						Token Purchase Form
					</Typography>
                    <TextField
                        InputProps={{ disableUnderline: true }}
                        required
                        fullWidth
                        id="sigValue"
                        label="Enter the sigUSD value you are sending"
                        name="sigusd"
                        variant="filled"
                        sx={{ mb: 3 }}
                        onChange={handleChange}
                        error={formErrors.sigusd}
                        helperText={formErrors.sigusd && 'Must be a value below your approved amount'}
                    />

                    <FormControl
                        variant="filled" 
                        fullWidth
                        required
                        name="wallet"
                        error={formErrors.wallet}
                    >
                        <InputLabel htmlFor="ergoAddress" sx={{'&.Mui-focused': { color: 'text.secondary'}}}>
                            Ergo Wallet Address
                        </InputLabel>
                        <FilledInput
                            id="ergoAddress"
                            value={wallet}
                            onClick={openWalletAdd}
                            readOnly
                            disableUnderline={true}
                            name="wallet"
                            type="ergoAddress"
                            sx={{ 
                                width: '100%', 
                                border: '1px solid rgba(82,82,90,1)', 
                                borderRadius: '4px', 
                            }}
                        />
                        <FormHelperText>
                            {formErrors.wallet && 'Your address must be approved on the whitelist' }
                        </FormHelperText>
                    </FormControl>

                    <FormControl required error={checkboxError}>
                    <FormGroup sx={{mt: 6 }}>
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={legal} 
                                    onChange={handleChecked} 
                                    name="legal" 
                                />
                            }
                            label="I have confirmed that I am legally entitled to invest in a cryptocurrency project of this nature in the jurisdiction in which I reside" 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={risks} 
                                    onChange={handleChecked} 
                                    name="risks" 
                                />
                            }
                            label="I am aware of the risks involved when investing in a project of this nature. There is always a chance an investment with this level of risk can lose all it's value, and I accept full responsiblity for my decision to invest in this project" 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={dao} 
                                    onChange={handleChecked} 
                                    name="dao" 
                                />
                            }
                            label="I understand that the funds raised by this project will be controlled by the ErgoPad DAO, which has board members throughout the world. I am aware that this DAO does not fall within the jurisdiction of any one country, and accept the implications therein." 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormHelperText>{checkboxError && 'Please accept the terms before submitting'}</FormHelperText>
                    </FormGroup>
                    </FormControl>

                    <Button
                            type="submit"
                            fullWidth
                            disabled={buttonDisabled}
                            //disabled={true}
                            variant="contained"
                            sx={{ mt: 3, mb: 2 }}
                    >
                        Submit
                    </Button>
                    {isLoading && (
                        <CircularProgress
                            size={24}
                            sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                marginTop: '-9px',
                                marginLeft: '-12px',
                            }}
                        />
                    )}
				</Box>

                <Snackbar open={openError} autoHideDuration={6000} onClose={handleCloseError}>
                    <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
                        {errorMessage}
                    </Alert>
                </Snackbar>
                <Dialog
                    open={openSuccess}
                    onClose={handleCloseSuccess}
                    aria-labelledby="alert-dialog-title"
                    aria-describedby="alert-dialog-description"
                >
                    <DialogTitle id="alert-dialog-title">
                        Transaction Approved
                    </DialogTitle>
                    <DialogContent>
                        <DialogContentText id="alert-dialog-description">
                            <Typography>Click on the amount and the address to copy them!</Typography>
                            <Typography>Please send exactly {successMessage.ergs} to {successMessage.address}</Typography>
                        </DialogContentText>
                        <Image src="/qr.png" alt="qr code" layout="responsive" width="400" height="400" />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseSuccess} autoFocus>
                            Close
                        </Button>
                    </DialogActions>
                </Dialog>

			</Grid>

        </Grid>
    </>
  );
};

export default Purchase;