import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import StatusBadge from '../src/components/StatusBadge';

describe('StatusBadge', () => {
  it('renders the status label for awaiting approval', () => {
    render(<StatusBadge status="awaiting_approval" />);
    expect(screen.getByText('待确认')).toBeInTheDocument();
  });

  it('renders the status label for approved', () => {
    render(<StatusBadge status="approved" />);
    expect(screen.getByText('已确认')).toBeInTheDocument();
  });
});
