import React, { useEffect, useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { BRAND_NAME, getRuntimeVersion, PRODUCER_NAME } from '../utils/appIdentity.ts';
import { rivarTokens } from '../theme/rivarTheme.ts';
import { useTranslation } from 'react-i18next';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [appVersion, setAppVersion] = useState<string>('...');

  const { login } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const isRTL = i18n.language?.startsWith('fa');

  useEffect(() => {
    let mounted = true;
    getRuntimeVersion().then((v) => { if (mounted) setAppVersion(v); });
    return () => { mounted = false; };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login({ username, password });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: rivarTokens.surface,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
        direction: isRTL ? 'rtl' : 'ltr',
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 400 }}>
        {/* Card */}
        <Box
          sx={{
            background: rivarTokens.paper,
            border: `1px solid ${rivarTokens.line}`,
            borderRadius: rivarTokens.radiusLg,
            boxShadow: rivarTokens.shadowPanel,
            p: { xs: 3, sm: 4 },
          }}
        >
          {/* Logo only — name is in the logo image */}
          <Box display="flex" flexDirection="column" alignItems="center" mb={3.5}>
            <Box
              component="img"
              src="/rivar.png"
              alt="Rivar logo"
              sx={{ width: 72, height: 72, objectFit: 'contain' }}
            />
          </Box>

          {/* Heading */}
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 600,
              color: rivarTokens.ink,
              mb: 0.5,
              textAlign: isRTL ? 'right' : 'left',
            }}
          >
            {t('auth.signInHeading')}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: rivarTokens.ink500,
              mb: 2.5,
              textAlign: isRTL ? 'right' : 'left',
            }}
          >
            {t('auth.signInPrompt')}
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label={t('auth.username')}
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label={t('auth.password')}
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                      aria-label="toggle password visibility"
                    >
                      {showPassword
                        ? <VisibilityOff sx={{ fontSize: 18 }} />
                        : <Visibility sx={{ fontSize: 18 }} />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading || !username || !password}
              sx={{ py: 1.25 }}
            >
              {loading
                ? <CircularProgress size={18} sx={{ color: '#fff' }} />
                : t('auth.signIn')}
            </Button>
          </Box>
        </Box>

        {/* Footer — version + brand */}
        <Box sx={{ mt: 2.5, textAlign: 'center' }}>
          <Typography variant="caption" sx={{ color: rivarTokens.ink300, display: 'block' }}>
            {BRAND_NAME}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              fontFamily: 'ui-monospace, monospace',
              color: rivarTokens.ink300,
              fontSize: '0.6875rem',
            }}
          >
            v{appVersion} · by {PRODUCER_NAME}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};
