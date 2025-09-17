import React from 'react';
import { render, screen } from '@testing-library/react';
import RewriteDisplay from '../RewriteDisplay';
import { SmartRewriteResponse } from '../../types/task';

describe('RewriteDisplay', () => {
    const mockRewrite: SmartRewriteResponse = {
        title: 'Enhanced Task: Implement User Authentication System',
        user_story: `As a developer, I want to implement a secure user authentication system so that users can safely access their accounts.

Acceptance Criteria:
- Users can register with email and password
- Users can log in with valid credentials
- Passwords are securely hashed and stored
- Session management is implemented
- Password reset functionality is available`
    };

    describe('Loading State', () => {
        it('should show loading spinner and message', () => {
            render(<RewriteDisplay loading={true} />);
            
            expect(screen.getByRole('progressbar')).toBeInTheDocument();
            expect(screen.getByText('Generating enhanced description...')).toBeInTheDocument();
            expect(screen.getByText('Enhanced Description')).toBeInTheDocument();
        });
    });

    describe('Error State', () => {
        it('should show error message', () => {
            const errorMessage = 'Failed to generate rewrite';
            render(<RewriteDisplay loading={false} error={errorMessage} />);
            
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(screen.getByText('Enhanced Description')).toBeInTheDocument();
            expect(screen.getByRole('alert')).toBeInTheDocument();
        });
    });

    describe('Success State', () => {
        it('should display enhanced title and user story', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            expect(screen.getByText('Enhanced Description')).toBeInTheDocument();
            expect(screen.getByText('Enhanced Title:')).toBeInTheDocument();
            expect(screen.getByText(mockRewrite.title)).toBeInTheDocument();
            expect(screen.getByText('User Story:')).toBeInTheDocument();
            expect(screen.getByText(/As a developer, I want to implement/)).toBeInTheDocument();
        });

        it('should preserve formatting in user story', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            // The user story should be displayed in a pre-formatted element
            const userStoryElement = screen.getByText(/As a developer, I want to implement/);
            expect(userStoryElement).toHaveStyle('white-space: pre-wrap');
            expect(userStoryElement).toHaveStyle('font-family: monospace');
        });

        it('should handle rewrite with only title', () => {
            const rewriteWithOnlyTitle = { title: 'Enhanced Title Only', user_story: '' };
            render(<RewriteDisplay rewrite={rewriteWithOnlyTitle} loading={false} />);
            
            expect(screen.getByText('Enhanced Title:')).toBeInTheDocument();
            expect(screen.getByText('Enhanced Title Only')).toBeInTheDocument();
            expect(screen.queryByText('User Story:')).not.toBeInTheDocument();
        });

        it('should handle rewrite with only user story', () => {
            const rewriteWithOnlyStory = { title: '', user_story: 'As a user, I want...' };
            render(<RewriteDisplay rewrite={rewriteWithOnlyStory} loading={false} />);
            
            expect(screen.queryByText('Enhanced Title:')).not.toBeInTheDocument();
            expect(screen.getByText('User Story:')).toBeInTheDocument();
            expect(screen.getByText('As a user, I want...')).toBeInTheDocument();
        });
    });

    describe('Conditional Rendering', () => {
        it('should not render when no rewrite is provided and not loading', () => {
            const { container } = render(<RewriteDisplay loading={false} />);
            expect(container.firstChild).toBeNull();
        });

        it('should render when rewrite is provided', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            expect(screen.getByText('Enhanced Description')).toBeInTheDocument();
        });

        it('should handle empty rewrite object', () => {
            const emptyRewrite = { title: '', user_story: '' };
            render(<RewriteDisplay rewrite={emptyRewrite} loading={false} />);
            
            expect(screen.getByText('Enhanced Description')).toBeInTheDocument();
            expect(screen.queryByText('Enhanced Title:')).not.toBeInTheDocument();
            expect(screen.queryByText('User Story:')).not.toBeInTheDocument();
        });
    });

    describe('Visual Elements', () => {
        it('should display the Edit icon', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            // The icon should be present in the header
            const header = screen.getByText('Enhanced Description').closest('div');
            expect(header).toBeInTheDocument();
        });

        it('should have proper card and paper structure', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            // Should be wrapped in a card
            const card = screen.getByText('Enhanced Description').closest('[class*="MuiCard"]');
            expect(card).toBeInTheDocument();
            
            // Content should be in paper elements
            const papers = screen.getAllByText(mockRewrite.title).map(el => 
                el.closest('[class*="MuiPaper"]')
            );
            expect(papers[0]).toBeInTheDocument();
        });

        it('should have proper styling for content sections', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            const titleElement = screen.getByText(mockRewrite.title);
            expect(titleElement).toHaveStyle('font-weight: 500'); // medium weight
            
            const userStoryElement = screen.getByText(/As a developer, I want to implement/);
            expect(userStoryElement).toHaveStyle('font-family: monospace');
        });
    });

    describe('Content Handling', () => {
        it('should handle long titles properly', () => {
            const longTitle = 'This is a very long enhanced title that should wrap properly and not break the layout of the component';
            const rewriteWithLongTitle = { ...mockRewrite, title: longTitle };
            render(<RewriteDisplay rewrite={rewriteWithLongTitle} loading={false} />);
            
            expect(screen.getByText(longTitle)).toBeInTheDocument();
        });

        it('should handle user stories with special characters', () => {
            const storyWithSpecialChars = `As a user, I want to "save & load" my data so that I can continue my work.

Acceptance Criteria:
- Save functionality works with special chars: @#$%^&*()
- Load handles UTF-8 characters: éñüñ
- Error handling for invalid characters`;
            
            const rewriteWithSpecialChars = { ...mockRewrite, user_story: storyWithSpecialChars };
            render(<RewriteDisplay rewrite={rewriteWithSpecialChars} loading={false} />);
            
            expect(screen.getByText(/As a user, I want to "save & load"/)).toBeInTheDocument();
        });

        it('should handle multiline user stories', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            // Check that the multiline content is preserved
            expect(screen.getByText(/As a developer, I want to implement/)).toBeInTheDocument();
            expect(screen.getByText(/Acceptance Criteria:/)).toBeInTheDocument();
            expect(screen.getByText(/Users can register with email/)).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('should have proper heading structure', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            const heading = screen.getByRole('heading', { level: 6 });
            expect(heading).toHaveTextContent('Enhanced Description');
        });

        it('should have accessible error alert', () => {
            render(<RewriteDisplay loading={false} error="Test error" />);
            
            const alert = screen.getByRole('alert');
            expect(alert).toHaveTextContent('Test error');
        });

        it('should have accessible loading indicator', () => {
            render(<RewriteDisplay loading={true} />);
            
            const progressBar = screen.getByRole('progressbar');
            expect(progressBar).toBeInTheDocument();
        });

        it('should have proper text contrast and readability', () => {
            render(<RewriteDisplay rewrite={mockRewrite} loading={false} />);
            
            // Labels should be properly marked
            expect(screen.getByText('Enhanced Title:')).toBeInTheDocument();
            expect(screen.getByText('User Story:')).toBeInTheDocument();
        });
    });
});