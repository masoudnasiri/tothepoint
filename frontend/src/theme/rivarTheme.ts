import { createTheme, Theme } from '@mui/material/styles';

// ─── Rivar Design Tokens ───────────────────────────────────────────────────
export const rivarTokens = {
  // Ink (text) scale
  ink: '#14181F',
  ink700: '#3A4150',
  ink500: '#5B6472',
  ink300: '#8A92A1',

  // Surface scale
  paper: '#FFFFFF',
  surface: '#F6F7F9',
  surface100: '#EEF0F3',

  // Line (border) scale
  line: '#E4E7EC',
  lineStrong: '#CBD0D9',

  // Accent
  accent: '#3651D4',
  accent600: '#2C44B8',
  accentTint: '#EEF1FD',
  accentTintStrong: '#DDE3FA',

  // Semantic
  good: '#1B7A4D',
  goodTint: '#E7F4EC',
  goodLine: '#BFE2CD',
  warn: '#B4740E',
  warnTint: '#FBF1E0',
  warnLine: '#F1D9A6',
  risk: '#C23A3A',
  riskTint: '#FBEAEA',
  riskLine: '#F2C3C3',

  // Radius
  radiusSm: '6px',
  radiusMd: '10px',
  radiusLg: '14px',

  // Shadow
  shadowCard: '0 1px 2px rgba(20,24,31,0.04), 0 1px 1px rgba(20,24,31,0.03)',
  shadowPanel: '0 1px 4px rgba(20,24,31,0.06), 0 1px 2px rgba(20,24,31,0.04)',

  // Sidebar
  sidebarWidth: 216,
} as const;

// ─── Font stacks (no external loading) ────────────────────────────────────
const fontUI = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const fontPersian = '"Yekan Bakh FaNum", Tahoma, Arial, sans-serif';

// ─── Theme factory ─────────────────────────────────────────────────────────
export const createRivarTheme = (isPersian: boolean = false, direction: 'ltr' | 'rtl' = 'ltr'): Theme => {
  const font = isPersian ? fontPersian : fontUI;

  return createTheme({
    direction,
    palette: {
      mode: 'light',
      primary: {
        main: rivarTokens.accent,
        dark: rivarTokens.accent600,
        light: rivarTokens.accentTint,
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: rivarTokens.ink700,
        contrastText: '#FFFFFF',
      },
      success: {
        main: rivarTokens.good,
        light: rivarTokens.goodTint,
      },
      warning: {
        main: rivarTokens.warn,
        light: rivarTokens.warnTint,
      },
      error: {
        main: rivarTokens.risk,
        light: rivarTokens.riskTint,
      },
      background: {
        default: rivarTokens.surface,
        paper: rivarTokens.paper,
      },
      text: {
        primary: rivarTokens.ink,
        secondary: rivarTokens.ink500,
        disabled: rivarTokens.ink300,
      },
      divider: rivarTokens.line,
    },

    typography: {
      fontFamily: font,
      h1: { fontFamily: font, fontWeight: 700, letterSpacing: '-0.02em' },
      h2: { fontFamily: font, fontWeight: 700, letterSpacing: '-0.015em' },
      h3: { fontFamily: font, fontWeight: 600, letterSpacing: '-0.01em' },
      h4: { fontFamily: font, fontWeight: 600, letterSpacing: '-0.01em', fontSize: '1.5rem' },
      h5: { fontFamily: font, fontWeight: 600, fontSize: '1.25rem' },
      h6: { fontFamily: font, fontWeight: 600, fontSize: '1.0625rem' },
      subtitle1: { fontFamily: font, fontWeight: 500, fontSize: '0.9375rem' },
      subtitle2: { fontFamily: font, fontWeight: 500, fontSize: '0.8125rem', color: rivarTokens.ink500 },
      body1: { fontFamily: font, fontSize: '0.875rem' },
      body2: { fontFamily: font, fontSize: '0.8125rem', color: rivarTokens.ink500 },
      caption: { fontFamily: font, fontSize: '0.75rem', color: rivarTokens.ink300 },
      button: { fontFamily: font, fontWeight: 500, fontSize: '0.8125rem', textTransform: 'none' },
    },

    shape: {
      borderRadius: 10,
    },

    breakpoints: {
      values: { xs: 0, sm: 600, md: 960, lg: 1280, xl: 1920 },
    },

    components: {
      // ── CssBaseline ────────────────────────────────────────────────────
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            background: rivarTokens.surface,
            color: rivarTokens.ink,
            fontFamily: font,
            WebkitFontSmoothing: 'antialiased',
            MozOsxFontSmoothing: 'grayscale',
          },
          '*': { boxSizing: 'border-box' },
        },
      },

      // ── AppBar / Topbar ────────────────────────────────────────────────
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: rivarTokens.paper,
            color: rivarTokens.ink,
            borderBottom: `1px solid ${rivarTokens.line}`,
            boxShadow: 'none',
          },
        },
        defaultProps: { elevation: 0, color: 'transparent' },
      },

      // ── Drawer / Sidebar ───────────────────────────────────────────────
      MuiDrawer: {
        styleOverrides: {
          paper: {
            background: rivarTokens.paper,
            borderRight: `1px solid ${rivarTokens.line}`,
            boxShadow: 'none',
            width: rivarTokens.sidebarWidth,
          },
        },
      },

      // ── Card ───────────────────────────────────────────────────────────
      MuiCard: {
        styleOverrides: {
          root: {
            background: rivarTokens.paper,
            border: `1px solid ${rivarTokens.line}`,
            borderRadius: rivarTokens.radiusLg,
            boxShadow: rivarTokens.shadowCard,
            '&:hover': { boxShadow: rivarTokens.shadowPanel },
          },
        },
        defaultProps: { elevation: 0 },
      },

      MuiCardContent: {
        styleOverrides: {
          root: { padding: '18px 20px', '&:last-child': { paddingBottom: '18px' } },
        },
      },

      // ── Paper ──────────────────────────────────────────────────────────
      MuiPaper: {
        styleOverrides: {
          root: {
            background: rivarTokens.paper,
            border: `1px solid ${rivarTokens.line}`,
            borderRadius: rivarTokens.radiusLg,
            boxShadow: rivarTokens.shadowCard,
          },
          outlined: {
            border: `1px solid ${rivarTokens.line}`,
            boxShadow: 'none',
          },
        },
        defaultProps: { elevation: 0 },
      },

      // ── Buttons ────────────────────────────────────────────────────────
      MuiButton: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontWeight: 500,
            fontSize: '0.8125rem',
            borderRadius: rivarTokens.radiusSm,
            padding: '8px 14px',
            textTransform: 'none',
            boxShadow: 'none',
            '&:hover': { boxShadow: 'none' },
          },
          contained: {
            background: rivarTokens.accent,
            color: '#FFFFFF',
            border: `1px solid ${rivarTokens.accent}`,
            '&:hover': { background: rivarTokens.accent600 },
          },
          outlined: {
            border: `1px solid ${rivarTokens.lineStrong}`,
            color: rivarTokens.ink,
            '&:hover': {
              background: rivarTokens.surface,
              border: `1px solid ${rivarTokens.ink300}`,
            },
          },
          text: {
            color: rivarTokens.ink700,
            '&:hover': { background: rivarTokens.surface },
          },
        },
        defaultProps: { disableElevation: true },
      },

      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: rivarTokens.radiusSm,
            color: rivarTokens.ink500,
            '&:hover': { background: rivarTokens.surface100 },
          },
        },
      },

      // ── Chip / Status pill ─────────────────────────────────────────────
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: '20px',
            fontWeight: 500,
            fontSize: '0.75rem',
            height: 24,
          },
          colorSuccess: {
            background: rivarTokens.goodTint,
            color: rivarTokens.good,
            border: `1px solid ${rivarTokens.goodLine}`,
          },
          colorWarning: {
            background: rivarTokens.warnTint,
            color: rivarTokens.warn,
            border: `1px solid ${rivarTokens.warnLine}`,
          },
          colorError: {
            background: rivarTokens.riskTint,
            color: rivarTokens.risk,
            border: `1px solid ${rivarTokens.riskLine}`,
          },
          colorPrimary: {
            background: rivarTokens.accentTint,
            color: rivarTokens.accent600,
            border: `1px solid ${rivarTokens.accentTintStrong}`,
          },
        },
      },

      // ── Tables ─────────────────────────────────────────────────────────
      MuiTableContainer: {
        styleOverrides: {
          root: {
            border: `1px solid ${rivarTokens.line}`,
            borderRadius: rivarTokens.radiusMd,
            overflow: 'hidden',
          },
        },
      },

      MuiTableHead: {
        styleOverrides: {
          root: { background: rivarTokens.surface },
        },
      },

      MuiTableCell: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontSize: '0.8125rem',
            borderBottom: `1px solid ${rivarTokens.line}`,
            padding: '12px 16px',
            color: rivarTokens.ink,
          },
          head: {
            fontWeight: 600,
            fontSize: '0.75rem',
            color: rivarTokens.ink500,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            padding: '10px 16px',
          },
        },
      },

      MuiTableRow: {
        styleOverrides: {
          root: {
            '&:hover': { background: rivarTokens.surface },
            '&:last-child td': { borderBottom: 'none' },
          },
        },
      },

      // ── Inputs ─────────────────────────────────────────────────────────
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiInputBase-root': {
              fontFamily: font,
              fontSize: '0.875rem',
              borderRadius: rivarTokens.radiusSm,
            },
          },
        },
        defaultProps: { size: 'small', variant: 'outlined' },
      },

      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: rivarTokens.radiusSm,
            '& fieldset': { borderColor: rivarTokens.lineStrong },
            '&:hover fieldset': { borderColor: rivarTokens.ink300 },
            '&.Mui-focused fieldset': { borderColor: rivarTokens.accent },
          },
        },
      },

      MuiInputLabel: {
        styleOverrides: {
          root: { fontFamily: font, fontSize: '0.875rem', color: rivarTokens.ink500 },
        },
      },

      MuiSelect: {
        styleOverrides: {
          select: { fontFamily: font, fontSize: '0.875rem' },
        },
        defaultProps: { size: 'small' },
      },

      MuiMenuItem: {
        styleOverrides: {
          root: { fontFamily: font, fontSize: '0.875rem' },
        },
      },

      // ── Toolbar ────────────────────────────────────────────────────────
      MuiToolbar: {
        styleOverrides: {
          root: { padding: '0 24px', minHeight: '56px !important' },
        },
      },

      // ── List nav items ─────────────────────────────────────────────────
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            margin: '1px 0',
            padding: '8px 10px',
            fontSize: '0.84375rem',
            fontWeight: 500,
            color: rivarTokens.ink700,
            '&:hover': { background: rivarTokens.surface },
            '&.Mui-selected': {
              background: rivarTokens.accentTint,
              color: rivarTokens.accent600,
              '&:hover': { background: rivarTokens.accentTintStrong },
              '& .MuiListItemIcon-root': { color: rivarTokens.accent600 },
            },
          },
        },
      },

      MuiListItemIcon: {
        styleOverrides: {
          root: {
            minWidth: 36,
            color: rivarTokens.ink300,
            '& svg': { fontSize: 17, opacity: 0.85 },
          },
        },
      },

      MuiListItemText: {
        styleOverrides: {
          primary: {
            fontFamily: font,
            fontWeight: 500,
            fontSize: '0.84375rem',
          },
        },
      },

      // ── Dialog ─────────────────────────────────────────────────────────
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: rivarTokens.radiusLg,
            border: `1px solid ${rivarTokens.line}`,
          },
        },
      },

      MuiDialogTitle: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontWeight: 600,
            fontSize: '1rem',
            padding: '20px 24px 14px',
            borderBottom: `1px solid ${rivarTokens.line}`,
          },
        },
      },

      MuiDialogContent: {
        styleOverrides: {
          root: { padding: '20px 24px', fontFamily: font },
        },
      },

      MuiDialogActions: {
        styleOverrides: {
          root: {
            padding: '14px 24px',
            borderTop: `1px solid ${rivarTokens.line}`,
            gap: 8,
          },
        },
      },

      // ── Accordion ──────────────────────────────────────────────────────
      MuiAccordion: {
        styleOverrides: {
          root: {
            border: `1px solid ${rivarTokens.line}`,
            borderRadius: `${rivarTokens.radiusMd} !important`,
            boxShadow: 'none',
            '&:before': { display: 'none' },
            marginBottom: 8,
          },
        },
      },

      MuiAccordionSummary: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontWeight: 600,
            fontSize: '0.875rem',
            minHeight: 48,
            padding: '0 16px',
          },
        },
      },

      // ── Alert ──────────────────────────────────────────────────────────
      MuiAlert: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontSize: '0.8125rem',
            borderRadius: rivarTokens.radiusMd,
          },
        },
      },

      // ── Tabs ───────────────────────────────────────────────────────────
      MuiTab: {
        styleOverrides: {
          root: {
            fontFamily: font,
            fontWeight: 500,
            fontSize: '0.8125rem',
            textTransform: 'none',
            minHeight: 40,
          },
        },
      },

      // ── Stepper ────────────────────────────────────────────────────────
      MuiStepLabel: {
        styleOverrides: {
          label: { fontFamily: font, fontWeight: 500, fontSize: '0.8125rem' },
        },
      },

      // ── Divider ────────────────────────────────────────────────────────
      MuiDivider: {
        styleOverrides: {
          root: { borderColor: rivarTokens.line },
        },
      },

      // ── Typography global ──────────────────────────────────────────────
      MuiTypography: {
        styleOverrides: {
          root: { fontFamily: font },
        },
      },

      // ── FormControl ────────────────────────────────────────────────────
      MuiFormControl: {
        styleOverrides: {
          root: { fontFamily: font },
        },
      },
    },
  });
};
