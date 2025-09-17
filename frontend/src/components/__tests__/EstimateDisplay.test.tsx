import React from 'react';
import { render, screen } from '@testing-library/react';
import EstimateDisplay from '../EstimateDisplay';
import { SmartEstimateResponse } from '../../types/task';

describe('EstimateDisplay', () => {
    const mockEstimate: SmartEstimateResponse = {
        suggested_points: 5,
        confidence: 0.75,
        similar_task_ids: [
            '123e4567-e89b-12d3-a456-426614174000',
            '456e7890-e89b-12d3-a456-426614174001',
            '789e0123-e89b-12d3-a456-426614174002'
        ],
        rationale: 'Based on similar tasks with same assignee and overlapping tags'
    };

    describe('Loading State', () => {
        it('should show loading spinner and message', () => {
            render(<EstimateDisplay loading={true} />);
            
            expect(screen.getByRole('progressbar')).toBeInTheDocument();
            expect(screen.getByText('Calculating estimate...')).toBeInTheDocument();
            expect(screen.getByText('Suggested Estimate')).toBeInTheDocument();
        });
    });

    describe('Error State', () => {
        it('should show error message', () => {
            const errorMessage = 'Failed to calculate estimate';
            render(<EstimateDisplay loading={false} error={errorMessage} />);
            
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(screen.getByText('Suggested Estimate')).toBeInTheDocument();
        });
    });

    describe('Success State', () => {
        it('should display estimate details correctly', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            expect(screen.getByText('Suggested Estimate')).toBeInTheDocument();
            expect(screen.getByText('5 Points')).toBeInTheDocument();
            expect(screen.getByText('Confidence: 75%')).toBeInTheDocument();
            expect(screen.getByText(mockEstimate.rationale)).toBeInTheDocument();
        });

        it('should display confidence progress bar with correct color', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toHaveAttribute('aria-valuenow', '75');
        });

        it('should show high confidence color for confidence >= 0.7', () => {
            const highConfidenceEstimate = { ...mockEstimate, confidence: 0.8 };
            render(<EstimateDisplay estimate={highConfidenceEstimate} loading={false} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toHaveClass('MuiLinearProgress-colorSuccess');
        });

        it('should show medium confidence color for confidence >= 0.5', () => {
            const mediumConfidenceEstimate = { ...mockEstimate, confidence: 0.6 };
            render(<EstimateDisplay estimate={mediumConfidenceEstimate} loading={false} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toHaveClass('MuiLinearProgress-colorWarning');
        });

        it('should show low confidence color for confidence < 0.5', () => {
            const lowConfidenceEstimate = { ...mockEstimate, confidence: 0.3 };
            render(<EstimateDisplay estimate={lowConfidenceEstimate} loading={false} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toHaveClass('MuiLinearProgress-colorError');
        });
    });

    describe('Similar Tasks Display', () => {
        it('should display similar tasks with correct count', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            expect(screen.getByText('Similar Tasks (3):')).toBeInTheDocument();
        });

        it('should display task links with shortened IDs', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            // Check for shortened task IDs (first 8 characters)
            expect(screen.getByText('Task 123e4567...')).toBeInTheDocument();
            expect(screen.getByText('Task 456e7890...')).toBeInTheDocument();
            expect(screen.getByText('Task 789e0123...')).toBeInTheDocument();
        });

        it('should display numbered chips for each similar task', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            expect(screen.getByText('#1')).toBeInTheDocument();
            expect(screen.getByText('#2')).toBeInTheDocument();
            expect(screen.getByText('#3')).toBeInTheDocument();
        });

        it('should create correct links to similar tasks', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            const links = screen.getAllByRole('link');
            expect(links[0]).toHaveAttribute('href', '/tasks/123e4567-e89b-12d3-a456-426614174000');
            expect(links[1]).toHaveAttribute('href', '/tasks/456e7890-e89b-12d3-a456-426614174001');
            expect(links[2]).toHaveAttribute('href', '/tasks/789e0123-e89b-12d3-a456-426614174002');
        });

        it('should not display similar tasks section when no similar tasks exist', () => {
            const estimateWithoutSimilar = { ...mockEstimate, similar_task_ids: [] };
            render(<EstimateDisplay estimate={estimateWithoutSimilar} loading={false} />);
            
            expect(screen.queryByText(/Similar Tasks/)).not.toBeInTheDocument();
        });

        it('should handle single similar task correctly', () => {
            const estimateWithOneSimilar = { 
                ...mockEstimate, 
                similar_task_ids: ['123e4567-e89b-12d3-a456-426614174000'] 
            };
            render(<EstimateDisplay estimate={estimateWithOneSimilar} loading={false} />);
            
            expect(screen.getByText('Similar Tasks (1):')).toBeInTheDocument();
            expect(screen.getByText('#1')).toBeInTheDocument();
            expect(screen.queryByText('#2')).not.toBeInTheDocument();
        });
    });

    describe('Conditional Rendering', () => {
        it('should not render when no estimate is provided', () => {
            const { container } = render(<EstimateDisplay loading={false} />);
            expect(container.firstChild).toBeNull();
        });

        it('should handle estimate without rationale', () => {
            const estimateWithoutRationale = { ...mockEstimate, rationale: '' };
            render(<EstimateDisplay estimate={estimateWithoutRationale} loading={false} />);
            
            expect(screen.getByText('5 Points')).toBeInTheDocument();
            expect(screen.queryByText('Rationale:')).not.toBeInTheDocument();
        });

        it('should handle estimate without similar tasks', () => {
            const estimateWithoutSimilar = { 
                ...mockEstimate, 
                similar_task_ids: undefined as any 
            };
            render(<EstimateDisplay estimate={estimateWithoutSimilar} loading={false} />);
            
            expect(screen.getByText('5 Points')).toBeInTheDocument();
            expect(screen.queryByText(/Similar Tasks/)).not.toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('should have proper ARIA labels and roles', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toHaveAttribute('aria-valuenow', '75');
            expect(progressBar).toHaveAttribute('aria-valuemin', '0');
            expect(progressBar).toHaveAttribute('aria-valuemax', '100');
        });

        it('should have accessible link text', () => {
            render(<EstimateDisplay estimate={mockEstimate} loading={false} />);
            
            const links = screen.getAllByRole('link');
            links.forEach(link => {
                expect(link).toHaveAttribute('href');
                expect(link.textContent).toBeTruthy();
            });
        });
    });
});