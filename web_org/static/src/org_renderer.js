import {
    Component,
    onMounted,
    onWillStart,
    onWillUnmount,
    useEffect,
    useRef,
    useState,
} from '@odoo/owl';
import { ensureHighchartsLoaded } from './highcharts_loader';
import { useViewCompiler } from '@web/views/view_compiler';
import { KanbanCompiler } from '@web/views/kanban/kanban_compiler';
import { renderToString } from '@web/core/utils/render';
import { getFormattedValue } from '@web/views/utils';

const clamp = (value, min, max) => Math.max(min, Math.min(value, max));
const linkKey = (from, to) => `${from}->${to}`;

export class OrgRenderer extends Component {
    static template = 'web_org.OrgRenderer';
    static Compiler = KanbanCompiler;
    static props = {
        model: Object,
        archInfo: Object,
        templates: { type: Object, optional: true },
    };

    setup() {
        this.containerRef = useRef('chart');
        this.chart = null;
        this.highcharts = null;

        const { templates = {}, inverted, nodeWidth, nodeHeight, padding } = this.props.archInfo;
        this.nodeWidth = nodeWidth;
        this.nodeHeight = nodeHeight;
        this.padding = padding;

        this.state = useState({
            inverted,
            hideIsolatedNodes: false,
            hideDimmedNodes: false,
            selectedNodeId: null,
        });

        this.compiledTemplates = useViewCompiler(this.constructor.Compiler, templates);
        this.cardTemplate = this.compiledTemplates['org-box'] || Object.values(templates)[0];
        this._prepareCardTemplate();

        onWillStart(async () => {
            this.highcharts = await ensureHighchartsLoaded();
        });

        onMounted(() => this._renderChart());

        onWillUnmount(() => {
            this.chart?.destroy();
            this.chart = null;
        });

        useEffect(
            () => this._renderChart(),
            () => [
                this.props.model.data,
                this.state.inverted,
                this.state.hideDimmedNodes,
                this.state.hideIsolatedNodes,
                this.state.selectedNodeId,
            ]
        );

        this.selectNodeAndLinks = this.selectNodeAndLinks.bind(this);
    }

    openRecord() {
        this._openRecordForm(this.state.selectedNodeId);
    }

    toggleDimmedNodes() {
        this.state.hideDimmedNodes = !this.state.hideDimmedNodes;
    }

    toggleIsolatedNodes() {
        this.state.hideIsolatedNodes = !this.state.hideIsolatedNodes;
    }

    toggleOrientation() {
        this.state.inverted = !this.state.inverted;
    }

    // ---------- Helpers ----------

    _selectNode(nodeId) {
        if (this.state.selectedNodeId !== nodeId) {
            this.state.selectedNodeId = nodeId || null;
            return;
        }
        this.state.selectedNodeId = null;
        this.state.hideDimmedNodes = false;
    }

    _getRelated(nodeId) {
        if (!nodeId) return new Set();

        const links = this.props.model.data.links || [];

        const parents = new Set();
        const children = new Set();

        const collectParents = (id) => {
            for (const [from, to] of links) {
                if (to === id && !parents.has(from)) {
                    parents.add(from);
                    collectParents(from);
                }
            }
        };

        const collectChildren = (id) => {
            for (const [from, to] of links) {
                if (from === id && !children.has(to)) {
                    children.add(to);
                    collectChildren(to);
                }
            }
        };

        collectParents(nodeId);
        collectChildren(nodeId);

        return new Set([nodeId, ...parents, ...children]);
    }

    _getRenderingContext(record) {
        return {
            context: this.props.model.config.context,
            JSON,
            luxon,
            record,
            __comp__: Object.assign(Object.create(this), {
                this: this,
                props: { ...this.props, record },
                getFormattedValue: this.getFormattedValue,
            }),
            __record__: record,
        };
    }

    getNodeById(nodeId) {
        return this.props.model.data.nodesById[nodeId];
    }

    getFormattedValue(fieldId) {
        const { archInfo, record } = this.props;
        const fieldInfo = archInfo.fieldNodes[fieldId];
        return getFormattedValue(record, fieldInfo.name, fieldInfo);
    }

    removeIntermediateLinks(links) {
        const adjacency = new Map();
        for (const [from, to] of links) {
            if (!adjacency.has(from)) adjacency.set(from, new Set());
            adjacency.get(from).add(to);
        }

        const result = [];
        for (const [from, to] of links) {
            const children = adjacency.get(from) || new Set();
            const isIntermediate = Array.from(children).some(
                (mid) => adjacency.get(mid)?.has(to)
            );
            if (!isIntermediate) {
                result.push([from, to]);
            }
        }
        return result;
    }

    _prepareCardTemplate() {
        if (!this.cardTemplate) {
            this.renderCardHtml = null;
            return;
        }
        this.renderCardHtml = (node) => renderToString(this.cardTemplate, this._getRenderingContext(node.values));
    }

    _openRecordForm(resId) {
        if (resId) {
            this.env.services.action.switchView('form', { resId });
        }
    }

    _escapeHTML(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    _computeChartSize(depth, maxBreadth, isVertical) {
        const baseWidth = isVertical ? maxBreadth : depth;
        const baseHeight = isVertical ? depth : maxBreadth;

        const chartWidth = clamp(baseWidth * (this.nodeWidth + this.padding), 200, 48000);
        const chartHeight = clamp(baseHeight * (this.nodeHeight + this.padding), 200, 48000);
        return { chartWidth, chartHeight };
    }

    _buildHighchartsNodes(nodes, relatedIds = new Set(), selectedId = null) {
        const hasImageField = !!this.props.archInfo.imageFieldName;
        const resModel = this.props.model.resModel;
        const imageField = this.props.model.imageField;
        const highlightMode = !!selectedId;

        return nodes.map((n) => {
            const isRelated = relatedIds.has(n.id);
            const isSelected = n.id === selectedId;
            const isDimmed = highlightMode && !isRelated;
            const status = isSelected ? 'selected' : isRelated ? 'related' : isDimmed ? 'dimmed' : 'normal';

            const point = {
                id: n.id,
                name: n.name,
                tooltip: n.tooltip,
                height: this.nodeHeight,
                status,
                isSelected,
                isRelated,
                isDimmed,
                values: n.values,
            };

            if (hasImageField) {
                point.image = `/web/image/${resModel}/${n.id}/${imageField}`;
            }
            if (this.renderCardHtml) {
                point.cardHtml = this.renderCardHtml(n);
            }
            return point;
        });
    }

    _buildHighchartsSeries(data, relatedIds = new Set()) {
        return data.map(([from, to]) => ({
            from,
            to,
            color: relatedIds.has(from) && relatedIds.has(to) ? '#3b82f6' : 'rgba(0, 0, 0, 0.15)',
        }));
    }

    selectNodeAndLinks(chart = null, nodeId) {
        const targetChart = chart || this.chart;
        const series = targetChart?.series?.[0];
        if (!series) return;

        series.points.forEach((p) => {
            p.setState('');
            p.selected = false;
        });

        const node = series.nodes.find((n) => n.id === nodeId);
        if (!node) return;

        node.select(true, false);

        const relatedIds = this._getRelated(nodeId);
        series.points.forEach((p) => {
            if (!p.isNode && p.graphic) {
                const related = relatedIds.has(p.from) && relatedIds.has(p.to);
                p.graphic.addClass(related ? 'highcharts-path-highlight' : 'highcharts-path-dimmed');
            }
        });
    }

    get relatedIds() {
        return this._getRelated(this.state.selectedNodeId);
    }

    get links() {
        const data = this.props.model.data || {};
        const relatedIds = this.relatedIds;

        let result = data.nonIsolatedLinks || [];
        if (this.state.hideDimmedNodes && relatedIds.size) {
            result = result.filter((l) => relatedIds.has(l[0]) && relatedIds.has(l[1]));
        }

        result = this.removeIntermediateLinks(result);

        if (!this.state.hideIsolatedNodes && data.isolatedLinks) {
            let isolated = data.isolatedLinks;
            if (this.state.hideDimmedNodes && relatedIds.size) {
                isolated = isolated.filter((l) => relatedIds.has(l[0]) && relatedIds.has(l[1]));
            }
            result = [...result, ...isolated];
        }

        return result;
    }

    get nodes() {
        let result = this.props.model.data.nodes || [];
        if (this.state.hideIsolatedNodes) {
            result = result.filter((n) => !n.isolated);
        }
        if (this.state.hideDimmedNodes) {
            const relatedIds = this.relatedIds;
            result = result.filter((n) => relatedIds.has(n.id));
        }
        return result;
    }

    // ---------- Main render ----------

    _renderChart() {
        if (!this.highcharts) return;

        const el = this.containerRef.el;
        if (!el) return;

        const links = this.links;
        const nodes = this.nodes || [];

        if (!nodes.length) {
            this.chart?.destroy();
            this.chart = null;
            el.innerHTML = '';
            return;
        }

        const isVerticalView = this.state.inverted;
        this.chart?.destroy();
        this.chart = null;

        const Highcharts = this.highcharts;
        const renderer = this;
        const selectedId = this.state.selectedNodeId;
        const relatedIds = this._getRelated(selectedId);
        const seriesData = this._buildHighchartsSeries(links, relatedIds);
        const highNodes = this._buildHighchartsNodes(nodes, relatedIds, selectedId);
        const escapeHTML = (txt) => this._escapeHTML(txt);

        this.chart = Highcharts.chart(el, {
            chart: {
                inverted: isVerticalView,
                animation: false,
                backgroundColor: 'transparent',
                events: {
                    load: function () {
                        const series = this.series[0];
                        const levelCounts = {};

                        (series.nodes || []).forEach((node) => {
                            const level = node.column || 0;
                            levelCounts[level] = (levelCounts[level] || 0) + 1;
                        });

                        const depth = Object.keys(levelCounts).length || 1;
                        const maxBreadth = Math.max(...Object.values(levelCounts));
                        const { chartWidth, chartHeight } = renderer._computeChartSize(
                            depth,
                            maxBreadth,
                            isVerticalView
                        );
                        el.style.width = `${chartWidth}px`;
                        el.style.height = `${chartHeight}px`;
                    },
                    render: function () {
                        renderer.selectNodeAndLinks(this, selectedId);
                    },
                },
            },
            title: { text: '' },
            credits: { enabled: false },

            tooltip: {
                outside: true,
                useHTML: true,
                style: { zIndex: 9999 },
                formatter: function () {
                    const p = this.point;
                    const label = p.isNode
                        ? p.tooltip || p.name
                        : `${p.fromNode.name} → ${p.toNode.name}`;
                    return `<div class="o_org_tooltip">${escapeHTML(label || '')}</div>`;
                },
            },

            series: [
                {
                    type: 'organization',
                    states: {
                        select: { color: '#ffcccc', borderColor: '#ff0000', lineWidth: 2 },
                    },
                    data: seriesData,
                    nodes: highNodes,
                    nodeWidth: this.state.inverted ? this.nodeHeight : this.nodeWidth,
                    borderColor: '#999999',
                    borderWidth: 1,
                    colorByPoint: false,
                    color: 'white',
                    dataLabels: {
                        useHTML: true,
                        padding: 0,
                        align: 'center',
                        verticalAlign: 'middle',
                        borderWidth: 0,
                        nodeFormatter: function () {
                            const point = this.point;
                            const extraClass = `o_org_node--${point.status}`;

                            if (point.cardHtml) {
                                return `
                                    <div class="o_org_node_inner ${extraClass}">
                                        ${point.cardHtml}
                                    </div>
                                `;
                            }

                            const name = escapeHTML(point.name || '');
                            const imgHtml = point.image
                                ? `
                                    <div class="o_org_node_img_wrap">
                                        <img src="${point.image}" alt="${name}" class="o_org_node_img"/>
                                    </div>
                                  `
                                : '';

                            return `
                                <div class="o_org_node_inner ${extraClass}">
                                    ${imgHtml}
                                    <div class="o_org_node_title">${name}</div>
                                </div>
                            `;
                        },
                        style: { textOutline: 'none' },
                    },
                },
            ],

            plotOptions: {
                series: {
                    animation: false,
                    linkOpacity: 0.7,
                    cursor: 'pointer',
                    nodeWidth: this.state.inverted ? this.nodeHeight : this.nodeWidth,
                    nodePadding: this.padding,
                    point: {
                        events: {
                            click: function () {
                                if (this.isNode) {
                                    renderer._selectNode(this.id);
                                }
                            },
                        },
                    },
                },
            },
        });

        setTimeout(() => this.chart?.reflow());
    }
}
