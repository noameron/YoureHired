import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentOutputCard from '@/components/AgentOutputCard.vue'

describe('AgentOutputCard', () => {
  describe('rendering', () => {
    it('renders article with class "agent-card"', () => {
      // GIVEN - the component is mounted with required props
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'pending',
          output: null
        }
      })

      // THEN - article element exists with correct class
      const article = wrapper.find('article')
      expect(article.exists()).toBe(true)
      expect(article.classes()).toContain('agent-card')
    })

    it('renders agent name in header', () => {
      // GIVEN - the component is mounted with a name
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Company Research',
          status: 'pending',
          output: null
        }
      })

      // THEN - name is displayed in h3 element
      const name = wrapper.find('h3.agent-name')
      expect(name.exists()).toBe(true)
      expect(name.text()).toBe('Company Research')
    })
  })

  describe('status: pending', () => {
    it('applies "pending" class to card', () => {
      // GIVEN - status is pending
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'pending',
          output: null
        }
      })

      // THEN - card has pending class
      expect(wrapper.find('article').classes()).toContain('pending')
    })

    it('displays circle SVG icon', () => {
      // GIVEN - status is pending
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'pending',
          output: null
        }
      })

      // THEN - pending icon (circle) is visible
      const svg = wrapper.find('svg.icon-pending')
      expect(svg.exists()).toBe(true)
      expect(svg.find('circle').exists()).toBe(true)
    })

    it('displays "Waiting..." text', () => {
      // GIVEN - status is pending
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'pending',
          output: null
        }
      })

      // THEN - waiting text is displayed
      const statusText = wrapper.find('.status-text.muted')
      expect(statusText.exists()).toBe(true)
      expect(statusText.text()).toBe('Waiting...')
    })
  })

  describe('status: running', () => {
    it('applies "running" class to card', () => {
      // GIVEN - status is running
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null
        }
      })

      // THEN - card has running class
      expect(wrapper.find('article').classes()).toContain('running')
    })

    it('displays spinner element', () => {
      // GIVEN - status is running
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null
        }
      })

      // THEN - spinner is visible
      const spinner = wrapper.find('.spinner')
      expect(spinner.exists()).toBe(true)
    })

    it('does not display SVG icon', () => {
      // GIVEN - status is running
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null
        }
      })

      // THEN - no SVG icons are visible
      expect(wrapper.find('svg').exists()).toBe(false)
    })

    it('displays default "Processing..." text when no streamingMessage', () => {
      // GIVEN - status is running without streamingMessage
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null
        }
      })

      // THEN - default processing text is displayed
      const statusText = wrapper.find('.status-text')
      expect(statusText.exists()).toBe(true)
      expect(statusText.text()).toBe('Processing...')
    })

    it('displays streamingMessage when provided', () => {
      // GIVEN - status is running with streamingMessage
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null,
          streamingMessage: 'Analyzing company data...'
        }
      })

      // THEN - streaming message is displayed
      const statusText = wrapper.find('.status-text')
      expect(statusText.exists()).toBe(true)
      expect(statusText.text()).toBe('Analyzing company data...')
    })

    it('has streaming-text class when running', () => {
      // GIVEN - status is running
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'running',
          output: null
        }
      })

      // THEN - status text has streaming-text class for animation
      const statusText = wrapper.find('.status-text')
      expect(statusText.classes()).toContain('streaming-text')
    })
  })

  describe('status: complete', () => {
    it('applies "complete" class to card', () => {
      // GIVEN - status is complete
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: 'Task completed successfully'
        }
      })

      // THEN - card has complete class
      expect(wrapper.find('article').classes()).toContain('complete')
    })

    it('displays checkmark SVG icon', () => {
      // GIVEN - status is complete
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: 'Done'
        }
      })

      // THEN - complete icon (checkmark) is visible
      const svg = wrapper.find('svg.icon-complete')
      expect(svg.exists()).toBe(true)
      expect(svg.find('path').exists()).toBe(true)
    })

    it('displays output text when output is provided', () => {
      // GIVEN - status is complete with output
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: 'Research results are ready'
        }
      })

      // THEN - output text is displayed
      const outputText = wrapper.find('.output-text')
      expect(outputText.exists()).toBe(true)
      expect(outputText.text()).toBe('Research results are ready')
    })

    it('does not display output when output is null', () => {
      // GIVEN - status is complete but output is null
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: null
        }
      })

      // THEN - no output text is displayed
      expect(wrapper.find('.output-text').exists()).toBe(false)
    })
  })

  describe('status: error', () => {
    it('applies "error" class to card', () => {
      // GIVEN - status is error
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null,
          error: 'Something went wrong'
        }
      })

      // THEN - card has error class
      expect(wrapper.find('article').classes()).toContain('error')
    })

    it('displays X SVG icon', () => {
      // GIVEN - status is error
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null
        }
      })

      // THEN - error icon (X) is visible
      const svg = wrapper.find('svg.icon-error')
      expect(svg.exists()).toBe(true)
      expect(svg.find('path').exists()).toBe(true)
    })

    it('displays custom error message when provided', () => {
      // GIVEN - status is error with custom message
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null,
          error: 'Network connection failed'
        }
      })

      // THEN - custom error message is displayed
      const errorText = wrapper.find('.error-text')
      expect(errorText.exists()).toBe(true)
      expect(errorText.text()).toBe('Network connection failed')
    })

    it('displays default error message when error prop is not provided', () => {
      // GIVEN - status is error without error prop
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null
        }
      })

      // THEN - default error message is displayed
      const errorText = wrapper.find('.error-text')
      expect(errorText.exists()).toBe(true)
      expect(errorText.text()).toBe('An error occurred')
    })

    it('displays default error message when error prop is empty string', () => {
      // GIVEN - status is error with empty string error
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null,
          error: ''
        }
      })

      // THEN - default error message is displayed
      const errorText = wrapper.find('.error-text')
      expect(errorText.text()).toBe('An error occurred')
    })
  })

  describe('SVG icon attributes', () => {
    it('pending icon circle has correct attributes', () => {
      // GIVEN - status is pending
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'pending',
          output: null
        }
      })

      // THEN - circle has correct center and radius
      const circle = wrapper.find('circle')
      expect(circle.attributes('cx')).toBe('12')
      expect(circle.attributes('cy')).toBe('12')
      expect(circle.attributes('r')).toBe('10')
    })

    it('complete icon path has correct d attribute', () => {
      // GIVEN - status is complete
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: 'Done'
        }
      })

      // THEN - path has correct checkmark d attribute
      const path = wrapper.find('path')
      expect(path.attributes('d')).toBe('M20 6L9 17l-5-5')
    })

    it('error icon path has correct d attribute', () => {
      // GIVEN - status is error
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null
        }
      })

      // THEN - path has correct X d attribute
      const path = wrapper.find('path')
      expect(path.attributes('d')).toBe('M18 6L6 18M6 6l12 12')
    })
  })

  describe('edge cases', () => {
    it('handles long agent name', () => {
      // GIVEN - agent has a very long name
      const longName = 'This is a very long agent name that should still render correctly'
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: longName,
          status: 'pending',
          output: null
        }
      })

      // THEN - long name is rendered
      expect(wrapper.find('.agent-name').text()).toBe(longName)
    })

    it('handles long output text', () => {
      // GIVEN - output is very long
      const longOutput = 'A'.repeat(500)
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: longOutput
        }
      })

      // THEN - long output is rendered
      expect(wrapper.find('.output-text').text()).toBe(longOutput)
    })

    it('handles special characters in name', () => {
      // GIVEN - name contains special characters
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: '<script>alert("xss")</script>',
          status: 'pending',
          output: null
        }
      })

      // THEN - special characters are escaped (Vue handles this)
      const nameEl = wrapper.find('.agent-name')
      expect(nameEl.text()).toBe('<script>alert("xss")</script>')
    })

    it('handles special characters in error message', () => {
      // GIVEN - error contains special characters
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'error',
          output: null,
          error: '<b>Bold error</b>'
        }
      })

      // THEN - special characters are escaped
      expect(wrapper.find('.error-text').text()).toBe('<b>Bold error</b>')
    })

    it('renders only one icon at a time', () => {
      // GIVEN - component is mounted with a status
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status: 'complete',
          output: 'Done'
        }
      })

      // THEN - only one icon is visible
      const svgs = wrapper.findAll('svg')
      expect(svgs.length).toBe(1)
      expect(wrapper.find('.spinner').exists()).toBe(false)
    })
  })

  describe('status parametrized tests', () => {
    it.each([
      { status: 'pending' as const, expectedClass: 'pending' },
      { status: 'running' as const, expectedClass: 'running' },
      { status: 'complete' as const, expectedClass: 'complete' },
      { status: 'error' as const, expectedClass: 'error' }
    ])('applies "$expectedClass" class when status is "$status"', ({ status, expectedClass }) => {
      // GIVEN - component is mounted with specific status
      const wrapper = mount(AgentOutputCard, {
        props: {
          name: 'Test Agent',
          status,
          output: status === 'complete' ? 'Done' : null
        }
      })

      // THEN - correct class is applied
      expect(wrapper.find('article').classes()).toContain(expectedClass)
    })
  })
})
