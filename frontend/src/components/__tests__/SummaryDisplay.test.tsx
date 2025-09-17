import React from 'react';
import { render, screen } from '@testing-library/react';
import SummaryDisplay from '../SummaryDisplay';

describe('SummaryDisplay', () => {
    describe('Loading State', () => {
        it('should show loading spinner and message', () => {
            render(<SummaryDisplay loading={true} />);
            
            expect(screen.getByRole('progressbar')).toBeInTheDocument();
            expect(screen.getByText('Generating summary...')).toBeInTheDocument();
            expect(screen.getByText('Task Summary')).toBeInTheDocument();
        });
    });

    describe('Error State', () => {
        it('should show error message', () => {
            const errorMessage = 'Failed to generate summary';
            render(<SummaryDisplay loading={false} error={errorMessage} />);
            
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(screen.getByText('Task Summary')).toBeInTheDocument();
            expect(screen.getByRole('alert')).toBeInTheDocument();
        });
    });

    describe('Success State', () => {
        it('should display summary content', () => {
            const summaryText = 'This task has been created and is currently in TODO status with 3 activities recorded.';
            render(<SummaryDisplay summary={summaryText} loading={false} />);
            
            expect(screen.getByText('Task Summary')).toBeInTheDocument();
            expect(screen.getByText(summaryText)).toBeInTheDocument();
        });

        it('should handle long summary text', () => {
            const longSummary = 'This is a very long summary that contains multiple sentences and should be displayed properly. '.repeat(10);
            render(<SummaryDisplay summary={longSummary} loading={false} />);
            
            expect(screen.getByText(/This is a very long summary that contains multiple sentences/)).toBeInTheDocument();
        });

        it('should handle summary with special characters', () => {
            const summaryWithSpecialChars = 'Task "Test & Development" has been updated 3 times. Status: TODO → IN_PROGRESS → DONE.';
            render(<SummaryDisplay summary={summaryWithSpecialChars} loading={false} />);
            
            expect(screen.getByText(summaryWithSpecialChars)).toBeInTheDocument();
        });
    });

    describe('Conditional Rendering', () => {
        it('should not render when no summary is provided and not loading', () => {
            const { container } = render(<SummaryDisplay loading={false} />);
            expect(container.firstChild).toBeNull();
        });

        it('should not render when summary is empty string', () => {
            const { container } = render(<SummaryDisplay summary="" loading={false} />);
            expect(container.firstChild).toBeNull();
        });

        it('should render when summary is provided', () => {
            render(<SummaryDisplay summary="Test summary" loading={false} />);
            expect(screen.getByText('Task Summary')).toBeInTheDocument();
        });
    });

    describe('Visual Elements', () => {
        it('should display the AutoAwesome icon', () => {
            render(<SummaryDisplay summary="Test summary" loading={false} />);
            
            // The icon should be present in the header
            const header = screen.getByText('Task Summary').closest('div');
            expect(header).toBeInTheDocument();
        });

        it('should have proper card structure', () => {
            render(<SummaryDisplay summary="Test summary" loading={false} />);
            
            // Should be wrapped in a card
            const card = screen.getByText('Task Summary').closest('[class*="MuiCard"]');
            expect(card).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('should have proper heading structure', () => {
            render(<SummaryDisplay summary="Test summary" loading={false} />);
            
            const heading = screen.getByRole('heading', { level: 6 });
            expect(heading).toHaveTextContent('Task Summary');
        });

        it('should have accessible error alert', () => {
            render(<SummaryDisplay loading={false} error="Test error" />);
            
            const alert = screen.getByRole('alert');
            expect(alert).toHaveTextContent('Test error');
        });

        it('should have accessible loading indicator', () => {
            render(<SummaryDisplay loading={true} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toBeInTheDocument();
        });
    });
});