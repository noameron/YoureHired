import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentFlowchart from '../AgentFlowchart.vue'
import type { FlowchartAgent } from '../AgentFlowchart.vue'

describe('AgentFlowchart', () => {
  const createAgents = (count: number): FlowchartAgent[] => {
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      name: `Agent ${i + 1}`,
      status: 'pending' as const,
      output: null,
      streamingMessage: null
    }))
  }

  describe('rendering', () => {
    it('renders flowchart container', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(2) }
      })

      expect(wrapper.find('.flowchart-container').exists()).toBe(true)
    })

    it('renders all agents from the start', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(2) }
      })

      const steps = wrapper.findAll('.flowchart-step')
      expect(steps.length).toBe(2)
    })

    it('renders AgentOutputCard for each agent', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(2) }
      })

      const cards = wrapper.findAllComponents({ name: 'AgentOutputCard' })
      expect(cards.length).toBe(2)
    })

    it('renders connector between agents', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(2) }
      })

      const connectors = wrapper.findAll('.connector')
      expect(connectors.length).toBe(1)
    })

    it('does not render connector after last agent', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(3) }
      })

      const connectors = wrapper.findAll('.connector')
      expect(connectors.length).toBe(2)
    })
  })

  describe('connector states', () => {
    it('connector is not active when first agent is pending', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'pending', output: null },
        { id: 2, name: 'Agent 2', status: 'pending', output: null }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const connector = wrapper.find('.connector')
      expect(connector.classes()).not.toContain('active')
    })

    it('connector is not active when first agent is running', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'running', output: null },
        { id: 2, name: 'Agent 2', status: 'pending', output: null }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const connector = wrapper.find('.connector')
      expect(connector.classes()).not.toContain('active')
    })

    it('connector becomes active when first agent completes', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'complete', output: 'Done' },
        { id: 2, name: 'Agent 2', status: 'pending', output: null }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const connector = wrapper.find('.connector')
      expect(connector.classes()).toContain('active')
    })

    it('connector is active when second agent is running', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'complete', output: 'Done' },
        { id: 2, name: 'Agent 2', status: 'running', output: null }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const connector = wrapper.find('.connector')
      expect(connector.classes()).toContain('active')
    })
  })

  describe('props passing', () => {
    it('passes correct props to AgentOutputCard', () => {
      const agents: FlowchartAgent[] = [
        {
          id: 1,
          name: 'Company Research',
          status: 'running',
          output: null,
          streamingMessage: 'Analyzing...'
        },
        {
          id: 2,
          name: 'Drill Generation',
          status: 'pending',
          output: null,
          error: undefined
        }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const cards = wrapper.findAllComponents({ name: 'AgentOutputCard' })
      expect(cards[0].props('name')).toBe('Company Research')
      expect(cards[0].props('status')).toBe('running')
      expect(cards[0].props('streamingMessage')).toBe('Analyzing...')
      expect(cards[1].props('name')).toBe('Drill Generation')
      expect(cards[1].props('status')).toBe('pending')
    })

    it('passes error prop to AgentOutputCard', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'error', output: null, error: 'Failed to connect' }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const card = wrapper.findComponent({ name: 'AgentOutputCard' })
      expect(card.props('error')).toBe('Failed to connect')
    })
  })

  describe('edge cases', () => {
    it('handles single agent (no connectors)', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: createAgents(1) }
      })

      expect(wrapper.findAll('.flowchart-step').length).toBe(1)
      expect(wrapper.findAll('.connector').length).toBe(0)
    })

    it('handles empty agents array', () => {
      const wrapper = mount(AgentFlowchart, {
        props: { agents: [] }
      })

      expect(wrapper.findAll('.flowchart-step').length).toBe(0)
    })

    it('handles multiple connectors with mixed states', () => {
      const agents: FlowchartAgent[] = [
        { id: 1, name: 'Agent 1', status: 'complete', output: 'Done' },
        { id: 2, name: 'Agent 2', status: 'running', output: null },
        { id: 3, name: 'Agent 3', status: 'pending', output: null }
      ]
      const wrapper = mount(AgentFlowchart, {
        props: { agents }
      })

      const connectors = wrapper.findAll('.connector')
      expect(connectors.length).toBe(2)
      expect(connectors[0].classes()).toContain('active')
      expect(connectors[1].classes()).not.toContain('active')
    })
  })
})
