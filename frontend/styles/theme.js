import { createTheme, responsiveFontSizes } from '@mui/material/styles';
import { text } from 'dom-helpers';

// Create a theme instance.
let theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      // main: 'rgb(58, 186, 180)',
      main: '#3ABAB4',
      hover: '#4BD0C9',
      active: 'rgba(49, 151, 149, 0.25)'
    },
    secondary: {
      main: '#9f7aea',
      hover: '#B886F9',
      active: 'rgba(128, 90, 213, 0.25)',
    },
    tertiary: {
      main: '#667eea',
      active: 'rgba(90, 103, 216, 0.25)'
    },
    quaternary: {
      main: 'rgb(237, 100, 166)',
    },
    background: {
      paper: 'rgba(35, 35, 39, 1)',
      default: 'rgb( 29, 29, 32 )',
    },
    text: {
      primary: 'rgb(244, 244, 245)',
      secondary: 'rgb(162, 162, 168)',
      tertiary: 'rgb(228, 228, 231)'
    },
    action: {
      hover: '#ffffff',
      light: {},
    },
    greyButton: {
      background: 'rgb(46, 46, 51)',
      hover: 'rgba(63,62,68,255)'
    }
  },
  typography: {
    fontFamily: ['Inter', 'sans-serif'].join(','),
    },
  components: {
    // Name of the component
    MuiAccordion: {
      styleOverrides: {
        // Name of the slot
        root: {
          // Some CSS
          marginBottom: '1rem',
        },
      },
    },
    MuiAppBar: {
      variants: [
        {
          props: { color: 'background' },
          style: {
            background: 'rgb( 29, 29, 32 )'
          }
        }
      ]
    }
  },
});

theme.typography.h1 = {
  fontSize: '5rem',
  lineHeight: '1.1',
  color: theme.palette.text.primary,
  fontWeight: '700',
  letterSpacing: '-0.02em',
  marginBottom: '2rem',
  '@media (max-width:880px)': {
    fontSize: '4.71rem',
  },
  '@media (max-width:800px)': {
    fontSize: '3.9rem',
  },
};

theme.typography.h2 = {
  color: theme.palette.text.primary,
  fontWeight: '700',
  fontSize: '3.5rem',
  marginBottom: '1rem',
  '@media (max-width:880px)': {
    fontSize: '2.63rem',
  },
  lineHeight: '1.0',
  letterSpacing: '-0.02em',
};

theme.typography.h3 = {
  color: theme.palette.text.primary,
  letterSpacing: '-.02em',
  fontSize: '2.5rem',
  marginBottom: '1rem',
  fontWeight: '700',
};

theme.typography.h4 = {
  color: theme.palette.text.primary,
  letterSpacing: '-.02em',
  fontSize: '2rem',
  marginBottom: '1rem',
  fontWeight: '600',
};

theme.typography.h5 = {
  color: theme.palette.text.primary,
  letterSpacing: '-.02em',
  fontSize: '1.6rem',
  marginBottom: '1rem',
  fontWeight: '500',
};

theme.typography.h6 = {
  color: theme.palette.text.primary,
  letterSpacing: '-.02em',
  fontSize: '1.3rem',
  marginBottom: '1rem',
  fontWeight: '500',
};

theme.typography.subtitle1 = {
  fontSize: '1.25rem',
  lineHeight: '1.5',
  marginBottom: '1.5rem',
  letterSpacing: '-.02em',
  fontWeight: '400',
  fontFamily: 'Inter, sans-serif',
  color: theme.palette.text.secondary
}

theme.typography.p = {
  color: theme.palette.text.secondary,
  fontSize: '1.125rem',
  marginBottom: '2rem',
  display: 'block'
}
    
export default theme;
