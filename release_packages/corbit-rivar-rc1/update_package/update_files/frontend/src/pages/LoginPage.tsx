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
import { BRAND_NAME, getRuntimeVersion, PRODUCT_NAME, PRODUCER_NAME } from '../utils/appIdentity.ts';
import { rivarTokens } from '../theme/rivarTheme.ts';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [appVersion, setAppVersion] = useState<string>('...');

  const { login } = useAuth();
  const navigate = useNavigate();

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
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
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
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: 400,
        }}
      >
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
          {/* Logo + brand */}
          <Box display="flex" flexDirection="column" alignItems="center" mb={3.5}>
            <Box
              component="img"
              src="/rivar.png"
              alt="Rivar logo"
              sx={{
                width: 56,
                height: 56,
                objectFit: 'contain',
                mb: 1.5,
              }}
            />
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                color: rivarTokens.ink,
                letterSpacing: '-0.01em',
                mb: 0.25,
              }}
            >
              {PRODUCT_NAME}
            </Typography>
            <Typography
              sx={{
                fontFamily: 'ui-monospace, monospace',
                fontSize: '0.75rem',
                color: rivarTokens.ink300,
              }}
            >
              by {PRODUCER_NAME} · v{appVersion}
            </Typography>
          </Box>

          {/* Heading */}
          <Typography
            variant="subtitle1"
            sx={{ fontWeight: 600, color: rivarTokens.ink, mb: 0.5 }}
          >
            Sign in to your account
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: rivarTokens.ink500, mb: 2.5 }}
          >
            Enter your credentials to access {BRAND_NAME}.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
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
              label="Password"
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
                    >
                      {showPassword ? <VisibilityOff sx={{ fontSize: 18 }} /> : <Visibility sx={{ fontSize: 18 }} />}
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
              {loading ? <CircularProgress size={18} sx={{ color: '#fff' }} /> : 'Sign In'}
            </Button>
          </Box>
        </Box>

        {/* Footer */}
        <Typography
          variant="caption"
          sx={{ display: 'block', textAlign: 'center', mt: 2.5, color: rivarTokens.ink300 }}
        >
          {BRAND_NAME} — Enterprise procurement & cash flow management
        </Typography>
      </Box>
    </Box>
  );
};
