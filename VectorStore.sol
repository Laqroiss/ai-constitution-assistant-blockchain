// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract VectorStore {
    struct Vector {
        uint256 id;
        int16[] values;
    }

    mapping(uint256 => Vector) public vectors;
    uint256 public nextId = 0;

    function storeVector(int16[] memory _values) public {
        vectors[nextId] = Vector(nextId, _values);
        nextId++;
    }

    function getVector(uint256 id) public view returns (int16[] memory) {
        return vectors[id].values;
    }

    function getTotalVectors() public view returns (uint256) {
        return nextId;
    }
}
