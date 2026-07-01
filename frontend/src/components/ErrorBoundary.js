import React from 'react';
import { COLORS } from '../store/theme';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '100%', minHeight: 300, background: COLORS.bgModal, color: COLORS.text, fontFamily: 'sans-serif', padding: 20, textAlign: 'center'
        }}>
          <h1 style={{ fontSize: 24, marginBottom: 12 }}>Something went wrong</h1>
          <p style={{ color: COLORS.textSecondary, marginBottom: 20 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            style={{
              padding: '10px 24px', background: '#2563eb', color: '#fff', border: 'none',
              borderRadius: 6, cursor: 'pointer', fontSize: 14
            }}
          >
            Reload application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
