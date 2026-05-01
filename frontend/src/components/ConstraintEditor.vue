<script setup>
const constraints = defineModel({ type: Array, default: () => [] })

function addConstraint() {
  constraints.value.push({
    attribute_name: '',
    allowed_values_raw: '',
    constraint_type: 'min_diversity',
    constraint_value: 2,
  })
}

function removeConstraint(index) {
  constraints.value.splice(index, 1)
}

function getValuesCount(c) {
  return c.allowed_values_raw.split(/[,，]/).map(s => s.trim()).filter(s => s).length
}
</script>

<template>
  <div class="form-group">
    <label>多样性限定 <span class="optional">(可选)</span></label>
    <div v-if="constraints.length === 0" class="hint" style="margin-bottom: 8px;">暂未添加限定规则</div>
    <div v-for="(c, idx) in constraints" :key="idx" class="constraint-card">
      <button type="button" class="constraint-remove" @click="removeConstraint(idx)" title="删除此限定">&times;</button>
      <div class="constraint-row">
        <input v-model="c.attribute_name" type="text" placeholder="属性名（如：性别、部门、区县）" class="constraint-name" />
      </div>
      <div class="constraint-row">
        <input v-model="c.allowed_values_raw" type="text" placeholder="可选值，逗号分隔（如：男，女）" class="constraint-values" />
      </div>
      <div class="constraint-row constraint-detail">
        <span class="constraint-label">每组中该属性</span>
        <select v-model="c.constraint_type" class="constraint-type">
          <option value="min_diversity">至少</option>
          <option value="max_diversity">最多</option>
        </select>
        <span class="constraint-label">有</span>
        <input v-model.number="c.constraint_value" type="number"
          :min="c.constraint_type === 'min_diversity' ? 2 : 1"
          :max="c.constraint_type === 'min_diversity' ? Math.max(getValuesCount(c), 2) : Math.max(getValuesCount(c) - 1, 1)"
          class="constraint-value" />
        <span class="constraint-label">种不同值</span>
      </div>
    </div>
    <button type="button" class="btn-add-constraint" @click="addConstraint">+ 添加限定规则</button>
  </div>
</template>

<style scoped>
.optional {
  font-size: 11px;
  color: #aaa;
  font-weight: 400;
}

.hint {
  font-size: 12px;
  color: #aaa;
}

.constraint-card {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  background: #fafafa;
}

.constraint-row {
  margin-bottom: 8px;
}

.constraint-row:last-child {
  margin-bottom: 0;
}

.constraint-name {
  width: 100%;
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.constraint-name:focus {
  border-color: #4f46e5;
}

.constraint-remove {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 28px;
  height: 28px;
  border: none;
  background: #fff;
  color: #999;
  font-size: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.constraint-remove:hover {
  color: #dc2626;
  background: #fef2f2;
}

.constraint-values {
  width: 100%;
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.constraint-values:focus {
  border-color: #4f46e5;
}

.constraint-detail {
  display: flex;
  align-items: center;
  gap: 6px;
}

.constraint-label {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.constraint-type {
  width: 64px;
  height: 32px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 6px;
  font-size: 12px;
  outline: none;
  background: #fff;
  cursor: pointer;
}

.constraint-type:focus {
  border-color: #4f46e5;
}

.constraint-value {
  width: 52px;
  height: 32px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 6px;
  font-size: 13px;
  text-align: center;
  outline: none;
  transition: border-color 0.2s;
}

.constraint-value:focus {
  border-color: #4f46e5;
}

.btn-add-constraint {
  display: inline-block;
  height: 32px;
  border: 1px dashed #ccc;
  border-radius: 6px;
  background: none;
  color: #888;
  font-size: 12px;
  cursor: pointer;
  padding: 0 12px;
  transition: all 0.2s;
}

.btn-add-constraint:hover {
  border-color: #4f46e5;
  color: #4f46e5;
}
</style>
